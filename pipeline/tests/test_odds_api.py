from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from pipeline.src.odds import odds_api


def test_parse_odds_response_normalizes_fixture(monkeypatch):
    raw = json.loads((Path(__file__).parent / "fixtures" / "odds_api_sample.json").read_text())
    monkeypatch.setattr(odds_api, "find_game_id", lambda **_: "game-123", raising=False)

    rows = odds_api.parse_odds_response(raw)

    assert len(rows) == 6
    assert {r.market for r in rows} == {"moneyline", "runline", "total"}
    assert all(r.game_id == "game-123" for r in rows)


def test_implied_probability_is_inverse(monkeypatch):
    raw = [{
        "home_team": "A", "away_team": "B", "commence_time": "2026-05-04T00:00:00Z",
        "bookmakers": [{"key": "draftkings", "markets": [{"key": "h2h", "outcomes": [{"name": "A", "price": 2.0}]}]}],
    }]
    monkeypatch.setattr(odds_api, "find_game_id", lambda **_: "gid", raising=False)
    row = odds_api.parse_odds_response(raw)[0]
    assert abs(row.implied_probability - (1 / row.decimal_odds)) < 0.0001


def test_decimal_to_american_conversion():
    assert odds_api._decimal_to_american(1.91) == -110
    assert odds_api._decimal_to_american(2.15) == 115


def test_run_daily_snapshot_skips_if_cache_exists(tmp_path, monkeypatch):
    cache = tmp_path / "2026-05-04" / "raw_odds.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("[]")

    monkeypatch.setattr(odds_api, "RAW_CACHE_ROOT", tmp_path)
    monkeypatch.setattr(odds_api, "_today_utc", lambda: datetime(2026, 5, 4, tzinfo=UTC).date())
    called = {"fetch": False}
    monkeypatch.setattr(odds_api, "fetch_mlb_odds", lambda: called.__setitem__("fetch", True), raising=True)

    assert odds_api.run_daily_snapshot() == 0
    assert called["fetch"] is False


def test_run_daily_snapshot_skips_if_db_has_today(monkeypatch):
    class Resp:
        count = 1

    class Table:
        def select(self, *args, **kwargs): return self
        def gte(self, *args, **kwargs): return self
        def lt(self, *args, **kwargs): return self
        def limit(self, *args, **kwargs): return self
        def execute(self): return Resp()

    class Client:
        def table(self, name): return Table()

    monkeypatch.setattr(odds_api, "_cache_file_for_day", lambda day=None: Path("/tmp/does-not-exist.json"))
    monkeypatch.setattr(odds_api, "get_supabase", lambda: Client(), raising=False)

    assert odds_api.run_daily_snapshot() == 0
