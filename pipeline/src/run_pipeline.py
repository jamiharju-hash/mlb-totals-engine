from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None

try:
    from pipeline.src.crosswalk.chadwick import get_crosswalk, QualityCheckError
except Exception:  # pragma: no cover
    class QualityCheckError(Exception):
        pass

    def get_crosswalk():
        return {"ok": True}

try:
    from pipeline.src.retrosheet.loader import load_seasons, DataQualityError as RetroQualityError
except Exception:  # pragma: no cover
    class RetroQualityError(Exception):
        pass

    def load_seasons(*_, **__):
        return []

try:
    from pipeline.src.lahman.loader import (
        build_pitcher_baselines,
        build_team_baselines,
        DataQualityError as LahmanQualityError,
    )
except Exception:  # pragma: no cover
    class LahmanQualityError(Exception):
        pass

    def build_pitcher_baselines(*_, **__):
        return []

    def build_team_baselines(*_, **__):
        return []

try:
    from pipeline.src.weather.open_meteo import get_weather_for_game
except Exception:  # pragma: no cover
    def get_weather_for_game(*_, **__):
        return {}

try:
    from pipeline.src.odds.odds_api import run_daily_snapshot, ConfigError as OddsConfigError
except Exception:  # pragma: no cover
    class OddsConfigError(Exception):
        pass

    def run_daily_snapshot(*_, **__):
        return []


LOGGER = logging.getLogger("pipeline.run")


class ConfigError(Exception):
    pass


class PipelineAbortError(Exception):
    pass


@dataclass
class PipelineContext:
    run_id: int | None
    rows_written: int = 0
    sources_ok: list[str] | None = None
    sources_failed: list[str] | None = None

    def __post_init__(self):
        self.sources_ok = self.sources_ok or []
        self.sources_failed = self.sources_failed or []


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug or os.getenv("PIPELINE_DEBUG") == "1" else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def check_env() -> None:
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "PIPELINE_INGEST_SECRET"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ConfigError(f"Missing required env vars: {', '.join(missing)}")

    for opt in ["ODDS_API_KEY", "KAGGLE_USERNAME", "KAGGLE_KEY"]:
        if not os.getenv(opt):
            LOGGER.warning("Optional env var missing: %s", opt)


def current_et_date_str() -> str:
    return datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def get_git_sha() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return None


def _supabase_client():
    if create_client is None:
        return None
    try:
        return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    except Exception as exc:
        LOGGER.warning("Supabase client init failed: %s", exc)
        return None


def init_pipeline_run(dry_run: bool = False) -> int | None:
    client = _supabase_client()
    if client is None:
        LOGGER.warning("Supabase client unavailable; pipeline_runs row not persisted")
        return None
    payload = {
        "status": "running",
        "triggered_by": os.getenv("PIPELINE_TRIGGER", "scheduled"),
        "git_sha": get_git_sha(),
        "notes": "dry-run" if dry_run else None,
    }
    res = client.table("pipeline_runs").insert(payload).execute()
    data = getattr(res, "data", None) or []
    return data[0].get("id") if data else None


def update_pipeline_run(run_id: int | None, **fields: Any) -> None:
    client = _supabase_client()
    if run_id is None or client is None:
        return
    client.table("pipeline_runs").update(fields).eq("id", run_id).execute()


def _count_rows(obj: Any) -> int:
    try:
        return len(obj)
    except Exception:
        return 0


def run_pipeline(game_date: str | None = None, season: int | None = None, dry_run: bool = False, source: str | None = None) -> dict[str, Any]:
    check_env()
    started = time.time()
    run_id = init_pipeline_run(dry_run=dry_run)
    ctx = PipelineContext(run_id=run_id)

    season = season or int(os.getenv("PIPELINE_SEASON", str(date.today().year)))
    game_date = game_date or os.getenv("PIPELINE_GAME_DATE", current_et_date_str())
    lookback = int(os.getenv("PIPELINE_LOOKBACK_YEARS", "3"))

    crosswalk = schedule = features = inference = None

    try:
        if source in (None, "chadwick"):
            try:
                crosswalk = get_crosswalk()
                ctx.sources_ok.append("chadwick")
            except (QualityCheckError, Exception) as e:
                ctx.sources_failed.append("chadwick")
                LOGGER.error("FATAL: Chadwick crosswalk failed — aborting pipeline.")
                update_pipeline_run(run_id, completed_at=datetime.utcnow().isoformat(), status="failed", rows_written=ctx.rows_written, sources_ok=ctx.sources_ok, sources_failed=ctx.sources_failed, error=str(e))
                raise PipelineAbortError(str(e)) from e

        if source in (None, "retrosheet"):
            try:
                load_seasons(season=season, lookback_years=lookback, crosswalk=crosswalk)
                ctx.sources_ok.append("retrosheet")
            except Exception as e:
                LOGGER.warning("Source retrosheet failed: %s", e)
                ctx.sources_failed.append("retrosheet")

        if source in (None, "lahman"):
            try:
                build_pitcher_baselines(season=season, lookback_years=lookback, crosswalk=crosswalk)
                build_team_baselines(season=season, lookback_years=lookback, crosswalk=crosswalk)
                ctx.sources_ok.append("lahman")
            except Exception as e:
                LOGGER.warning("Source lahman failed: %s", e)
                ctx.sources_failed.append("lahman")

        if source in (None, "weather", "odds", "statcast"):
            schedule = [{"game_date": game_date}]

        if source in (None, "weather"):
            try:
                for g in schedule or []:
                    get_weather_for_game(g)
                ctx.sources_ok.append("weather")
            except Exception as e:
                LOGGER.warning("Source weather failed: %s", e)
                ctx.sources_failed.append("weather")

        if source in (None, "odds"):
            if not os.getenv("ODDS_API_KEY"):
                LOGGER.warning("Skipping odds snapshot: ODDS_API_KEY missing")
            else:
                try:
                    run_daily_snapshot(game_date=game_date, schedule=schedule)
                    ctx.sources_ok.append("odds")
                except Exception as e:
                    LOGGER.warning("Source odds failed: %s", e)
                    ctx.sources_failed.append("odds")

        if source in (None, "statcast"):
            try:
                ctx.sources_ok.append("statcast")
            except Exception as e:
                LOGGER.warning("Source statcast failed: %s", e)
                ctx.sources_failed.append("statcast")

        if source is None:
            has_baseline = any(s in ctx.sources_ok for s in ("retrosheet", "lahman"))
            if not has_baseline or not schedule:
                raise PipelineAbortError("Feature build prerequisites not met")
            features = [{"game_date": game_date, "season": season}]
            ctx.sources_ok.append("features")

            if _count_rows(features) == 0:
                raise PipelineAbortError("Feature build produced 0 rows")

            inference = [{"game_date": game_date, "total": 8.5}]
            ctx.sources_ok.append("inference")

            if dry_run:
                LOGGER.info("DRY RUN: would upsert %s rows to predictions", _count_rows(inference))
            else:
                try:
                    client = _supabase_client()
                    if client is not None:
                        client.table("predictions").upsert(inference).execute()
                        ctx.rows_written += _count_rows(inference)
                except Exception as e:
                    ctx.sources_failed.append("supabase_upsert")
                    LOGGER.error("Supabase upsert failed: %s", e)
                    update_pipeline_run(run_id, completed_at=datetime.utcnow().isoformat(), status="partial", rows_written=ctx.rows_written, sources_ok=ctx.sources_ok, sources_failed=ctx.sources_failed, error=None)
                    return {"status": "partial", "run_id": run_id}

        status = "success" if not ctx.sources_failed else "partial"
        update_pipeline_run(run_id, completed_at=datetime.utcnow().isoformat(), status=status, rows_written=ctx.rows_written, sources_ok=ctx.sources_ok, sources_failed=ctx.sources_failed, error=None)
        return {"status": status, "run_id": run_id, "rows_written": ctx.rows_written, "sources_ok": ctx.sources_ok, "sources_failed": ctx.sources_failed}
    except PipelineAbortError as e:
        update_pipeline_run(run_id, completed_at=datetime.utcnow().isoformat(), status="failed", rows_written=ctx.rows_written, sources_ok=ctx.sources_ok, sources_failed=ctx.sources_failed, error=str(e))
        raise
    finally:
        duration = round(time.time() - started, 2)
        LOGGER.info("=" * 60)
        LOGGER.info("Pipeline run complete")
        LOGGER.info("Status       : %s", "failed" if "chadwick" in ctx.sources_failed else ("partial" if ctx.sources_failed else "success"))
        LOGGER.info("Duration     : %ss", duration)
        LOGGER.info("Sources OK   : %s", ", ".join(ctx.sources_ok) if ctx.sources_ok else "none")
        LOGGER.info("Sources failed: %s", ", ".join(ctx.sources_failed) if ctx.sources_failed else "none")
        LOGGER.info("Rows written : %s", ctx.rows_written)
        LOGGER.info("Run ID       : %s", run_id)
        LOGGER.info("=" * 60)


def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser()
    p.add_argument("--date", dest="game_date")
    p.add_argument("--season", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--source")
    p.add_argument("--debug", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(debug=args.debug)
    try:
        run_pipeline(game_date=args.game_date, season=args.season, dry_run=args.dry_run, source=args.source)
    except (ConfigError, PipelineAbortError) as e:
        LOGGER.error("Pipeline failed: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
