from pathlib import Path

import pandas as pd
import pytest

from pipeline.src.lahman.loader import DataQualityError, build_pitcher_baselines, load_pitching, load_teams


@pytest.fixture
def setup_lahman_files(tmp_path, monkeypatch):
    sample = Path("pipeline/tests/fixtures/lahman_pitching_sample.csv")
    pitching = tmp_path / "Pitching.csv"
    pitching.write_text(sample.read_text())

    people = tmp_path / "People.csv"
    people.write_text("playerID,bbrefID\np1,bb1\np2,bb2\np3,bb3\np4,bb4\n")

    teams = tmp_path / "Teams.csv"
    teams.write_text("yearID,teamID,W,L,R,RA,ERA,attendance\n2020,MON,70,92,700,800,4.80,1200000\n")

    files = {
        "Pitching": pitching,
        "People": people,
        "Teams": teams,
        "Batting": tmp_path / "Batting.csv",
        "Fielding": tmp_path / "Fielding.csv",
    }
    for k in ["Batting", "Fielding"]:
        files[k].write_text("x\n")

    monkeypatch.setattr("pipeline.src.lahman.loader.download_lahman_files", lambda: files)
    monkeypatch.setattr(
        "pipeline.src.lahman.loader.get_crosswalk",
        lambda: pd.DataFrame({"key_bbref": ["bb1", "bb2", "bb3", "bb4"], "key_mlbam": ["1001", "1002", "1003", "1004"]}),
    )


def test_load_pitching_computed_rates(setup_lahman_files):
    df = load_pitching([2020])
    r = df[df["playerID"] == "p1"].iloc[0]
    assert r["whip"] == pytest.approx((4 + 10) / 10)
    assert r["k_per_9"] == pytest.approx((12 / 10) * 9)
    assert r["fip"] == pytest.approx((13 * 2 + 3 * 4 - 2 * 12) / 10 + 3.10)


def test_zero_ip_rows_no_div_zero(setup_lahman_files):
    df = load_pitching([2020])
    r = df[df["playerID"] == "p2"].iloc[0]
    assert pd.isna(r["whip"])
    assert pd.isna(r["k_per_9"])
    assert pd.isna(r["fip"])


def test_team_code_normalization_mon_to_wsn(setup_lahman_files):
    teams = load_teams([2020])
    assert teams.iloc[0]["team_id"] == "WSN"


def test_build_pitcher_baselines_aggregates_multi_team(setup_lahman_files):
    df = build_pitcher_baselines([2020])
    p1 = df[df["playerID"] == "p1"].iloc[0]
    assert p1["innings_pitched"] == pytest.approx(15.0)
    assert p1["games"] == 15


def test_data_quality_error_for_era_out_of_range(tmp_path, monkeypatch):
    pitching = tmp_path / "Pitching.csv"
    pitching.write_text("playerID,yearID,teamID,G,GS,IPouts,H,ER,HR,BB,SO,ERA\np1,2020,MON,1,1,3,1,1,0,1,1,30.0\n")
    people = tmp_path / "People.csv"
    people.write_text("playerID,bbrefID\np1,bb1\n")
    teams = tmp_path / "Teams.csv"
    teams.write_text("yearID,teamID,W,L,R,RA,ERA,attendance\n2020,MON,1,1,1,1,1.0,1\n")
    files = {"Pitching": pitching, "People": people, "Teams": teams, "Batting": tmp_path / "Batting.csv", "Fielding": tmp_path / "Fielding.csv"}
    files["Batting"].write_text("x\n")
    files["Fielding"].write_text("x\n")
    monkeypatch.setattr("pipeline.src.lahman.loader.download_lahman_files", lambda: files)
    monkeypatch.setattr("pipeline.src.lahman.loader.get_crosswalk", lambda: pd.DataFrame({"key_bbref": ["bb1"], "key_mlbam": ["1001"]}))
    with pytest.raises(DataQualityError):
        load_pitching([2020])
