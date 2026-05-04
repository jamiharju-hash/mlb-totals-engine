from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import requests

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"
BOOKMAKER_PRIORITY = ["draftkings", "fanduel", "betmgm", "caesars", "bovada"]
RAW_CACHE_ROOT = Path(__file__).resolve().parents[2] / "data" / "raw" / "odds"
BUDGET_CACHE_FILE = RAW_CACHE_ROOT / "budget_status.json"


class ConfigError(RuntimeError):
    pass


@dataclass
class OddsSnapshot:
    snapshot_id: str
    fetched_at: datetime
    game_id: str
    home_team: str
    away_team: str
    commence_time: datetime
    bookmaker: str
    market: Literal["moneyline", "runline", "total"]
    selection: str
    decimal_odds: float
    american_odds: int
    implied_probability: float
    source: str = "the-odds-api"


def _today_utc() -> date:
    return datetime.now(UTC).date()


def _cache_file_for_day(day: date | None = None) -> Path:
    day = day or _today_utc()
    return RAW_CACHE_ROOT / day.isoformat() / "raw_odds.json"


def _decimal_to_american(decimal_odds: float) -> int:
    if decimal_odds >= 2.0:
        return round((decimal_odds - 1.0) * 100)
    return round(-100.0 / (decimal_odds - 1.0))


def fetch_mlb_odds() -> list[dict[str, Any]]:
    cache_file = _cache_file_for_day()
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise ConfigError("ODDS_API_KEY is required")

    response = requests.get(
        f"{BASE_URL}/sports/baseball_mlb/odds/",
        params={
            "apiKey": api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        },
        timeout=30,
    )
    response.raise_for_status()

    remaining = int(response.headers.get("x-requests-remaining", "-1"))
    used = int(response.headers.get("x-requests-used", "-1"))
    LOGGER.info("Odds API usage: remaining=%s used=%s", remaining, used)
    if 0 <= remaining < 50:
        LOGGER.warning("Odds API remaining request budget is low: %s", remaining)

    payload = response.json()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(payload, indent=2))
    return payload


def _normalize_market_key(key: str) -> str | None:
    return {"h2h": "moneyline", "spreads": "runline", "totals": "total"}.get(key)


def _find_game_id(home_team: str, away_team: str, commence: datetime) -> str | None:
    lookup = globals().get("find_game_id")
    if callable(lookup):
        return lookup(home_team=home_team, away_team=away_team, commence_time=commence)
    return None


def parse_odds_response(raw: list[dict[str, Any]]) -> list[OddsSnapshot]:
    rows: list[OddsSnapshot] = []
    fetched_at = datetime.now(UTC)

    for game in raw:
        bookmakers = game.get("bookmakers", [])
        selected = next((b for b in bookmakers if b.get("key") in BOOKMAKER_PRIORITY), None)
        if not selected:
            continue

        commence = datetime.fromisoformat(game["commence_time"].replace("Z", "+00:00"))
        game_id = _find_game_id(game["home_team"], game["away_team"], commence)
        if not game_id:
            LOGGER.warning(
                "No game_id match for %s vs %s (%s); skipping",
                game.get("away_team"),
                game.get("home_team"),
                commence.isoformat(),
            )
            continue

        for market_obj in selected.get("markets", []):
            market = _normalize_market_key(market_obj.get("key", ""))
            if market is None:
                continue
            for out in market_obj.get("outcomes", []):
                decimal_odds = float(out["price"])
                selection = str(out["name"]).lower() if market == "total" else str(out["name"])
                rows.append(
                    OddsSnapshot(
                        snapshot_id=str(uuid4()),
                        fetched_at=fetched_at,
                        game_id=game_id,
                        home_team=game["home_team"],
                        away_team=game["away_team"],
                        commence_time=commence,
                        bookmaker=selected["key"],
                        market=market,
                        selection=selection,
                        decimal_odds=decimal_odds,
                        american_odds=_decimal_to_american(decimal_odds),
                        implied_probability=1.0 / decimal_odds,
                    )
                )
    return rows


def _get_supabase_client() -> Any:
    getter = globals().get("get_supabase")
    if callable(getter):
        return getter()
    raise ConfigError("Supabase client getter not configured")


def upsert_snapshots(snapshots: list[OddsSnapshot]) -> int:
    if not snapshots:
        return 0
    rows = [asdict(s) for s in snapshots]
    client = _get_supabase_client()
    client.table("odds_snapshots").upsert(
        rows,
        on_conflict="game_id,bookmaker,market,selection,fetched_at",
    ).execute()
    return len(rows)


def get_budget_status() -> dict[str, float | int]:
    now = datetime.now(UTC)
    if BUDGET_CACHE_FILE.exists():
        cached = json.loads(BUDGET_CACHE_FILE.read_text())
        ts = datetime.fromisoformat(cached["cached_at"])
        if now - ts <= timedelta(hours=1):
            return cached["status"]

    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise ConfigError("ODDS_API_KEY is required")

    response = requests.get(f"{BASE_URL}/sports/", params={"apiKey": api_key}, timeout=30)
    response.raise_for_status()
    remaining = int(response.headers.get("x-requests-remaining", "0"))
    used = int(response.headers.get("x-requests-used", "0"))
    status = {"remaining": remaining, "used": used, "pct_used": (used / (used + remaining) * 100) if (used + remaining) else 0.0}

    BUDGET_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BUDGET_CACHE_FILE.write_text(json.dumps({"cached_at": now.isoformat(), "status": status}, indent=2))
    return status


def run_daily_snapshot() -> int:
    cache_file = _cache_file_for_day()
    if cache_file.exists():
        LOGGER.info("Daily odds snapshot already cached at %s; skipping", cache_file)
        return 0

    client = _get_supabase_client()
    today = _today_utc().isoformat()
    existing = (
        client.table("odds_snapshots")
        .select("snapshot_id", count="exact")
        .gte("fetched_at", f"{today}T00:00:00+00:00")
        .lt("fetched_at", f"{today}T23:59:59+00:00")
        .limit(1)
        .execute()
    )
    if getattr(existing, "count", 0):
        LOGGER.info("Today's odds snapshots already exist in DB; skipping")
        return 0

    if not os.getenv("ODDS_API_KEY"):
        raise ConfigError("ODDS_API_KEY is required")

    raw = fetch_mlb_odds()
    snapshots = parse_odds_response(raw)
    written = upsert_snapshots(snapshots)
    budget = get_budget_status()
    LOGGER.info(
        "Odds snapshot summary: games=%s rows_written=%s requests_remaining=%s",
        len(raw),
        written,
        budget["remaining"],
    )
    return written
