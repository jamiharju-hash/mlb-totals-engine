from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


REQUIRED_ODDS_FIELDS = {'line', 'over', 'under', 'timestamp'}


def _normalize_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str):
        return value
    raise ValueError('odds timestamp must be a datetime or ISO-8601 string')


def store_snapshot(db: Any, game_id: str, odds: Mapping[str, Any]) -> Any:
    """Persist one market totals snapshot.

    Expected db interface:
        db.insert(table_name: str, row: dict) -> Any

    Required odds fields:
        line: market total runs
        over: American odds for over
        under: American odds for under
        timestamp: snapshot timestamp
    """
    missing = REQUIRED_ODDS_FIELDS - set(odds.keys())
    if missing:
        raise ValueError(f'Missing odds fields: {sorted(missing)}')

    row = {
        'game_id': game_id,
        'line': float(odds['line']),
        'over': int(odds['over']),
        'under': int(odds['under']),
        'timestamp': _normalize_timestamp(odds['timestamp']),
    }
    return db.insert('odds_snapshots', row)
