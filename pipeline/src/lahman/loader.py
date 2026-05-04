from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.src.config import RAW_DIR
from pipeline.src.crosswalk.chadwick import get_crosswalk

LAHMAN_BASE_URL = "https://github.com/chadwickbureau/baseballdatabank/raw/master/core"
LAHMAN_FILES = ["People", "Pitching", "Batting", "Teams", "Fielding"]
CACHE_MAX_AGE_DAYS = 7
FIP_CONSTANT = 3.10


class DataQualityError(ValueError):
    pass


@dataclass
class PitcherSeason:
    playerID: str
    mlbam_id: int | None
    season: int
    team: str
    games: int
    games_started: int
    innings_pitched: float
    era: float | None
    whip: float | None
    k_per_9: float | None
    bb_per_9: float | None
    hr_per_9: float | None
    fip: float | None


@dataclass
class TeamSeason:
    team_id: str
    season: int
    wins: int
    losses: int
    runs_scored: int
    runs_allowed: int
    era: float | None
    attendance: int | None
    park_factor: float | None


TEAM_CODE_MAP = {
    "MON": "WSN", "FLO": "MIA", "ANA": "LAA", "TBA": "TB", "CAL": "LAA",
    "KCA": "KC", "SLN": "STL", "CHN": "CHC", "NYA": "NYY", "NYN": "NYM",
    "SDN": "SD", "SFN": "SF", "LAN": "LAD",
}


def _is_stale(path: Path, max_age_days: int = CACHE_MAX_AGE_DAYS) -> bool:
    if not path.exists():
        return True
    age_seconds = pd.Timestamp.utcnow().timestamp() - path.stat().st_mtime
    return age_seconds > max_age_days * 24 * 60 * 60


def download_lahman_files() -> dict[str, Path]:
    target_dir = RAW_DIR / "lahman"
    target_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for file_stem in LAHMAN_FILES:
        path = target_dir / f"{file_stem}.csv"
        if _is_stale(path):
            url = f"{LAHMAN_BASE_URL}/{file_stem}.csv"
            pd.read_csv(url).to_csv(path, index=False)
        paths[file_stem] = path
    return paths


def _rate_stat(num: pd.Series, ip: pd.Series, multiplier: float) -> pd.Series:
    out = np.where(ip > 0, (num / ip) * multiplier, np.nan)
    return pd.Series(out)


def _write_quarantine(unresolved: pd.DataFrame) -> None:
    if unresolved.empty:
        return
    out = unresolved[["playerID", "bbrefID"]].drop_duplicates().copy()
    out["source"] = "lahman"
    q_path = RAW_DIR / "lahman" / "player_crosswalk_quarantine.csv"
    q_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(q_path, index=False)


def load_pitching(seasons: list[int]) -> pd.DataFrame:
    files = download_lahman_files()
    pitching = pd.read_csv(files["Pitching"])
    people = pd.read_csv(files["People"], dtype={"playerID": str, "bbrefID": str})

    pitching = pitching[pitching["yearID"].isin(seasons)].copy()

    if pitching.duplicated(["playerID", "yearID", "teamID"]).any():
        raise DataQualityError("Duplicate (playerID, season, team) in Pitching.csv")

    pitching["IPouts"] = pd.to_numeric(pitching["IPouts"], errors="coerce").fillna(0)
    pitching["innings_pitched"] = pitching["IPouts"] / 3.0

    if (pitching["innings_pitched"] < 0).any():
        raise DataQualityError("Negative innings pitched found")

    for col in ["BB", "H", "SO", "HR", "G", "GS", "ERA"]:
        pitching[col] = pd.to_numeric(pitching.get(col), errors="coerce")

    ip = pitching["innings_pitched"]
    pitching["whip"] = np.where(ip > 0, (pitching["BB"] + pitching["H"]) / ip, np.nan)
    pitching["k_per_9"] = _rate_stat(pitching["SO"], ip, 9.0)
    pitching["bb_per_9"] = _rate_stat(pitching["BB"], ip, 9.0)
    pitching["hr_per_9"] = _rate_stat(pitching["HR"], ip, 9.0)
    pitching["fip"] = np.where(ip > 0, (13 * pitching["HR"] + 3 * pitching["BB"] - 2 * pitching["SO"]) / ip + FIP_CONSTANT, np.nan)

    era_mask = pitching["ERA"].notna()
    if ((pitching.loc[era_mask, "ERA"] < 0.0) | (pitching.loc[era_mask, "ERA"] > 27.0)).any():
        raise DataQualityError("ERA out of valid range [0, 27]")

    pitching = pitching.merge(people[["playerID", "bbrefID"]], on="playerID", how="left")
    cw = get_crosswalk()
    cw["mlbam_id"] = pd.to_numeric(cw["key_mlbam"], errors="coerce").astype("Int64")
    pitching = pitching.merge(cw[["key_bbref", "mlbam_id"]], left_on="bbrefID", right_on="key_bbref", how="left")

    unresolved = pitching[pitching["mlbam_id"].isna() & pitching["bbrefID"].notna()]
    _write_quarantine(unresolved)

    eligible = pitching[pitching["innings_pitched"] >= 10]
    if not eligible.empty:
        resolution_rate = eligible["mlbam_id"].notna().mean()
        if resolution_rate < 0.85:
            raise DataQualityError("Pitcher crosswalk resolution rate below 85% for IP>=10")

    return pitching.rename(columns={"yearID": "season", "teamID": "team", "ERA": "era", "G": "games", "GS": "games_started"})


def load_teams(seasons: list[int]) -> pd.DataFrame:
    files = download_lahman_files()
    teams = pd.read_csv(files["Teams"])
    teams = teams[teams["yearID"].isin(seasons)].copy()
    teams["team_id"] = teams["teamID"].astype(str).str.upper().replace(TEAM_CODE_MAP)
    teams["season"] = teams["yearID"].astype(int)
    teams["wins"] = pd.to_numeric(teams["W"], errors="coerce").fillna(0).astype(int)
    teams["losses"] = pd.to_numeric(teams["L"], errors="coerce").fillna(0).astype(int)
    teams["runs_scored"] = pd.to_numeric(teams["R"], errors="coerce").fillna(0).astype(int)
    teams["runs_allowed"] = pd.to_numeric(teams["RA"], errors="coerce").fillna(0).astype(int)
    teams["era"] = pd.to_numeric(teams.get("ERA"), errors="coerce")
    teams["attendance"] = pd.to_numeric(teams.get("attendance"), errors="coerce").astype("Int64")
    teams["park_factor"] = np.nan
    return teams[["team_id", "season", "wins", "losses", "runs_scored", "runs_allowed", "era", "attendance", "park_factor"]]


def build_pitcher_baselines(seasons: list[int]) -> pd.DataFrame:
    df = load_pitching(seasons)
    grouped = df.groupby(["playerID", "mlbam_id", "season"], dropna=False, as_index=False).agg(
        team_count=("team", "nunique"),
        games=("games", "sum"),
        games_started=("games_started", "sum"),
        innings_pitched=("innings_pitched", "sum"),
        hits=("H", "sum"),
        walks=("BB", "sum"),
        strikeouts=("SO", "sum"),
        home_runs=("HR", "sum"),
        earned_runs=("ER", "sum"),
    )
    ip = grouped["innings_pitched"]
    grouped["whip"] = np.where(ip > 0, (grouped["walks"] + grouped["hits"]) / ip, np.nan)
    grouped["k_per_9"] = np.where(ip > 0, (grouped["strikeouts"] / ip) * 9, np.nan)
    grouped["bb_per_9"] = np.where(ip > 0, (grouped["walks"] / ip) * 9, np.nan)
    grouped["hr_per_9"] = np.where(ip > 0, (grouped["home_runs"] / ip) * 9, np.nan)
    grouped["era"] = np.where(ip > 0, (grouped["earned_runs"] * 9) / ip, np.nan)
    grouped["fip"] = np.where(ip > 0, (13 * grouped["home_runs"] + 3 * grouped["walks"] - 2 * grouped["strikeouts"]) / ip + FIP_CONSTANT, np.nan)

    return grouped[grouped["mlbam_id"].notna()].drop(columns=["team_count"]).reset_index(drop=True)


def build_team_baselines(seasons: list[int]) -> pd.DataFrame:
    return load_teams(seasons)
