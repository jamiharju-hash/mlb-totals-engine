"""Retrosheet historical game log loader for MLB totals features."""

from __future__ import annotations

import csv
import logging
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from urllib.request import urlretrieve

import pandas as pd

from pipeline.src.crosswalk.chadwick import get_crosswalk

LOGGER = logging.getLogger(__name__)

RAW_DIR = Path("pipeline/data/raw/retrosheet/gamelogs")
FEATURE_DIR = Path("pipeline/data/features/retrosheet")


class DataQualityError(RuntimeError):
    """Raised when parsed Retrosheet data fails hard quality checks."""


@dataclass
class GameLog:
    game_id: str
    game_date: date
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    total_runs: int
    home_hits: int
    away_hits: int
    home_errors: int
    away_errors: int
    attendance: int | None
    game_duration_min: int | None
    day_night: Literal["D", "N"]
    park_id: str
    home_starter_retro_id: str | None
    away_starter_retro_id: str | None
    home_starter_mlbam_id: int | None
    away_starter_mlbam_id: int | None


def write_player_crosswalk_quarantine(retro_id: str, source: str = "retrosheet") -> None:
    """Write unresolved player IDs to quarantine sink (placeholder for Supabase)."""

    LOGGER.warning("unresolved retro_id=%s source=%s", retro_id, source)


def _parse_int(value: str) -> int | None:
    value = value.strip()
    return int(value) if value else None


def download_gamelogs(season: int) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / f"gl{season}.zip"
    txt_path = RAW_DIR / f"GL{season}.TXT"

    if txt_path.exists():
        return txt_path

    if not zip_path.exists():
        urlretrieve(f"https://www.retrosheet.org/gamelogs/gl{season}.zip", zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        target = next((n for n in zf.namelist() if n.upper().endswith(f"{season}.TXT")), None)
        if not target:
            raise FileNotFoundError(f"No TXT file found in {zip_path}")
        zf.extract(target, RAW_DIR)
        extracted = RAW_DIR / target
        if extracted != txt_path:
            extracted.rename(txt_path)
    return txt_path


def parse_gamelogs(path: Path, season: int) -> list[GameLog]:
    crosswalk = get_crosswalk()
    out: list[GameLog] = []
    resolved = 0
    starter_rows = 0

    with path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            game_date = datetime.strptime(row[0], "%Y%m%d").date()
            away_starter = row[101].strip() or None
            home_starter = row[103].strip() or None
            away_mlbam = crosswalk.resolve_retro(away_starter)
            home_mlbam = crosswalk.resolve_retro(home_starter)

            for retro_id, resolved_id in ((away_starter, away_mlbam), (home_starter, home_mlbam)):
                if retro_id:
                    starter_rows += 1
                    if resolved_id is None:
                        write_player_crosswalk_quarantine(retro_id, source="retrosheet")
                    else:
                        resolved += 1

            away_score = int(row[9])
            home_score = int(row[10])
            out.append(
                GameLog(
                    game_id=f"{row[6]}{row[0]}{row[1] or '0'}",
                    game_date=game_date,
                    home_team=row[6],
                    away_team=row[3],
                    home_score=home_score,
                    away_score=away_score,
                    total_runs=home_score + away_score,
                    away_hits=int(row[26]),
                    home_hits=int(row[53]),
                    away_errors=int(row[35]),
                    home_errors=int(row[62]),
                    attendance=_parse_int(row[21]),
                    game_duration_min=_parse_int(row[22]),
                    day_night=(row[16] or "N"),
                    park_id=row[20],
                    home_starter_retro_id=home_starter,
                    away_starter_retro_id=away_starter,
                    home_starter_mlbam_id=home_mlbam,
                    away_starter_mlbam_id=away_mlbam,
                )
            )

    _run_quality_checks(out, season)
    if starter_rows:
        rate = resolved / starter_rows
        if rate < 0.9:
            LOGGER.warning("Starter crosswalk resolution below threshold: %.2f%%", rate * 100)
    return out


def _run_quality_checks(rows: list[GameLog], season: int) -> None:
    ids = set()
    for g in rows:
        if g.home_score < 0 or g.away_score < 0:
            raise DataQualityError("Negative score found")
        if g.game_id in ids:
            raise DataQualityError("Duplicate game_id in season")
        ids.add(g.game_id)
        if g.total_runs != g.home_score + g.away_score:
            raise DataQualityError("total_runs mismatch")
        if g.game_date.year != season:
            raise DataQualityError("game_date outside requested season")


def load_season(season: int) -> list[GameLog]:
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = FEATURE_DIR / f"gamelogs_{season}.parquet"
    txt_path = download_gamelogs(season)

    if parquet_path.exists() and parquet_path.stat().st_mtime >= txt_path.stat().st_mtime:
        df = pd.read_parquet(parquet_path)
        return [GameLog(**{**r, "game_date": pd.to_datetime(r["game_date"]).date()}) for r in df.to_dict("records")]

    rows = parse_gamelogs(txt_path, season)
    df = pd.DataFrame([asdict(r) for r in rows])
    # Attribution: Retrosheet data used under free non-commercial license with attribution.
    df.to_parquet(parquet_path, index=False)
    return rows


def load_seasons(start: int, end: int) -> pd.DataFrame:
    frames = []
    for season in range(start, end + 1):
        rows = load_season(season)
        frame = pd.DataFrame([asdict(r) for r in rows])
        frame["season"] = season
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def compute_team_game_totals(df: pd.DataFrame) -> pd.DataFrame:
    home = pd.DataFrame(
        {
            "team": df["home_team"],
            "game_id": df["game_id"],
            "game_date": df["game_date"],
            "runs_scored": df["home_score"],
            "runs_allowed": df["away_score"],
            "total_runs": df["total_runs"],
            "win": (df["home_score"] > df["away_score"]).astype(int),
            "loss": (df["home_score"] < df["away_score"]).astype(int),
            "home_away": "home",
        }
    )
    away = pd.DataFrame(
        {
            "team": df["away_team"],
            "game_id": df["game_id"],
            "game_date": df["game_date"],
            "runs_scored": df["away_score"],
            "runs_allowed": df["home_score"],
            "total_runs": df["total_runs"],
            "win": (df["away_score"] > df["home_score"]).astype(int),
            "loss": (df["away_score"] < df["home_score"]).astype(int),
            "home_away": "away",
        }
    )
    return pd.concat([home, away], ignore_index=True)
