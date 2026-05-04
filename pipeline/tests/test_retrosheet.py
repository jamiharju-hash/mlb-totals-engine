import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))


import pandas as pd
import pytest

from pipeline.src.retrosheet import loader
from pipeline.src.retrosheet.loader import DataQualityError


def test_parse_gamelogs_fixture():
    rows = loader.parse_gamelogs(Path("pipeline/tests/fixtures/retrosheet_gl_sample.txt"), 2023)
    assert len(rows) == 3
    assert all(r.total_runs == r.home_score + r.away_score for r in rows)


def test_unresolved_quarantine(monkeypatch):
    seen = []

    monkeypatch.setattr(loader, "write_player_crosswalk_quarantine", lambda retro_id, source="retrosheet": seen.append((retro_id, source)))
    loader.parse_gamelogs(Path("pipeline/tests/fixtures/retrosheet_gl_sample.txt"), 2023)
    assert any(source == "retrosheet" for _, source in seen)


def test_load_seasons_season_column(monkeypatch):
    sample = loader.parse_gamelogs(Path("pipeline/tests/fixtures/retrosheet_gl_sample.txt"), 2023)
    monkeypatch.setattr(loader, "load_season", lambda season: sample)
    df = loader.load_seasons(2023, 2024)
    assert "season" in df.columns
    assert set(df["season"].unique()) == {2023, 2024}


def test_data_quality_error_total_runs_mismatch():
    rows = loader.parse_gamelogs(Path("pipeline/tests/fixtures/retrosheet_gl_sample.txt"), 2023)
    rows[0].total_runs += 1
    with pytest.raises(DataQualityError):
        loader._run_quality_checks(rows, 2023)