from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable

from app.clients.mlb_stats import MLBStatsClient
from app.clients.odds_api import OddsAPIClient
from app.config import get_settings
from app.db.supabase_admin import get_supabase_admin


@dataclass(frozen=True)
class NormalizedGame:
    game_id: str
    game_date: str
    game_datetime: str | None
    home_team: str
    away_team: str
    home_probable_pitcher: str | None
    away_probable_pitcher: str | None
    status: str
    home_runs: int | None
    away_runs: int | None
    total_runs: int | None


@dataclass(frozen=True)
class NormalizedOddsSnapshot:
    provider_game_id: str
    game_id: str | None
    home_team: str
    away_team: str
    bookmaker: str
    line: float
    over: int
    under: int
    timestamp: str
    market_phase: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _normalize_team_name(value: str) -> str:
    return ''.join(ch.lower() for ch in value if ch.isalnum())


def _market_phase(now: datetime | None = None) -> str:
    return 'unknown'


def normalize_mlb_schedule(payload: dict[str, Any]) -> list[NormalizedGame]:
    games: list[NormalizedGame] = []
    for day in payload.get('dates', []):
        game_date = day.get('date')
        for game in day.get('games', []):
            teams = game.get('teams', {})
            home = teams.get('home', {})
            away = teams.get('away', {})
            home_team = home.get('team', {})
            away_team = away.get('team', {})
            home_score = _safe_int(home.get('score'))
            away_score = _safe_int(away.get('score'))
            total_runs = None
            if home_score is not None and away_score is not None:
                total_runs = home_score + away_score

            games.append(
                NormalizedGame(
                    game_id=str(game.get('gamePk')),
                    game_date=str(game_date),
                    game_datetime=game.get('gameDate'),
                    home_team=home_team.get('name', ''),
                    away_team=away_team.get('name', ''),
                    home_probable_pitcher=(home.get('probablePitcher') or {}).get('fullName'),
                    away_probable_pitcher=(away.get('probablePitcher') or {}).get('fullName'),
                    status=(game.get('status') or {}).get('detailedState', ''),
                    home_runs=home_score,
                    away_runs=away_score,
                    total_runs=total_runs,
                )
            )
    return games


def build_game_lookup(games: Iterable[NormalizedGame]) -> dict[tuple[str, str, str], str]:
    lookup: dict[tuple[str, str, str], str] = {}
    for game in games:
        key = (
            str(game.game_date),
            _normalize_team_name(game.home_team),
            _normalize_team_name(game.away_team),
        )
        lookup[key] = game.game_id
    return lookup


def normalize_totals_odds(
    payload: Iterable[dict[str, Any]],
    game_lookup: dict[tuple[str, str, str], str] | None = None,
) -> list[NormalizedOddsSnapshot]:
    snapshots: list[NormalizedOddsSnapshot] = []
    lookup = game_lookup or {}
    for event in payload:
        home_team = event.get('home_team', '')
        away_team = event.get('away_team', '')
        provider_game_id = str(event.get('id'))
        commence_time = event.get('commence_time')
        game_date = str(commence_time).split('T')[0] if commence_time else ''
        game_id = lookup.get(
            (
                game_date,
                _normalize_team_name(home_team),
                _normalize_team_name(away_team),
            )
        )
        for bookmaker in event.get('bookmakers', []):
            bookmaker_key = bookmaker.get('key', '')
            timestamp = bookmaker.get('last_update') or _utc_now()
            for market in bookmaker.get('markets', []):
                if market.get('key') != 'totals':
                    continue
                outcomes = market.get('outcomes', [])
                over = next((o for o in outcomes if str(o.get('name')).lower() == 'over'), None)
                under = next((o for o in outcomes if str(o.get('name')).lower() == 'under'), None)
                if not over or not under:
                    continue
                line = over.get('point', under.get('point'))
                if line is None:
                    continue
                snapshots.append(
                    NormalizedOddsSnapshot(
                        provider_game_id=provider_game_id,
                        game_id=game_id,
                        home_team=home_team,
                        away_team=away_team,
                        bookmaker=bookmaker_key,
                        line=float(line),
                        over=int(over.get('price')),
                        under=int(under.get('price')),
                        timestamp=timestamp,
                        market_phase=_market_phase(),
                    )
                )
    return snapshots


def upsert_games(games: Iterable[NormalizedGame]) -> int:
    supabase = get_supabase_admin()
    rows = [
        {
            'id': game.game_id,
            'game_date': game.game_date,
            'game_datetime': game.game_datetime,
            'home_team': game.home_team,
            'away_team': game.away_team,
            'home_probable_pitcher': game.home_probable_pitcher,
            'away_probable_pitcher': game.away_probable_pitcher,
            'status': game.status,
            'updated_at': _utc_now(),
        }
        for game in games
        if game.game_id and game.game_id != 'None'
    ]
    if rows:
        supabase.table('games').upsert(rows, on_conflict='id').execute()
    return len(rows)


def insert_odds_snapshots(snapshots: Iterable[NormalizedOddsSnapshot]) -> int:
    supabase = get_supabase_admin()
    rows = [
        {
            'provider_game_id': snapshot.provider_game_id,
            'game_id': snapshot.game_id,
            'home_team': snapshot.home_team,
            'away_team': snapshot.away_team,
            'bookmaker': snapshot.bookmaker,
            'book': snapshot.bookmaker,
            'line': snapshot.line,
            'over': snapshot.over,
            'under': snapshot.under,
            'over_odds': snapshot.over,
            'under_odds': snapshot.under,
            'timestamp': snapshot.timestamp,
            'market_phase': snapshot.market_phase,
        }
        for snapshot in snapshots
    ]
    if rows:
        supabase.table('odds_snapshots').insert(rows).execute()
    return len(rows)


def upsert_game_results(games: Iterable[NormalizedGame]) -> int:
    supabase = get_supabase_admin()
    rows = [
        {
            'game_id': game.game_id,
            'home_score': game.home_runs,
            'away_score': game.away_runs,
            'home_runs': game.home_runs,
            'away_runs': game.away_runs,
            'total_runs': game.total_runs,
            'is_completed': True,
            'finalized_at': _utc_now(),
        }
        for game in games
        if game.total_runs is not None and game.status.lower() in {'final', 'game over'}
    ]
    if rows:
        supabase.table('game_results').upsert(rows, on_conflict='game_id').execute()
    return len(rows)


async def acquire_mlb_day(game_date: date) -> dict[str, int]:
    settings = get_settings()
    client = MLBStatsClient(settings.mlb_stats_api_base_url)
    payload = await client.schedule(game_date)
    games = normalize_mlb_schedule(payload)
    games_count = upsert_games(games)
    results_count = upsert_game_results(games)
    return {'games': games_count, 'results': results_count}


async def acquire_totals_market() -> dict[str, int]:
    settings = get_settings()
    mlb_client = MLBStatsClient(settings.mlb_stats_api_base_url)
    odds_client = OddsAPIClient(settings.odds_api_base_url, settings.odds_api_key)

    today_payload = await mlb_client.schedule(date.today())
    tomorrow_payload = await mlb_client.schedule(date.fromordinal(date.today().toordinal() + 1))
    games = normalize_mlb_schedule(today_payload) + normalize_mlb_schedule(tomorrow_payload)
    if games:
        upsert_games(games)

    payload = await odds_client.totals_odds(
        regions=settings.odds_regions,
        markets=settings.odds_markets,
        bookmakers=settings.odds_bookmakers,
    )
    snapshots = normalize_totals_odds(payload, build_game_lookup(games))
    inserted = insert_odds_snapshots(snapshots)
    linked = sum(1 for snapshot in snapshots if snapshot.game_id is not None)
    return {'odds_snapshots': inserted, 'linked_odds_snapshots': linked}
