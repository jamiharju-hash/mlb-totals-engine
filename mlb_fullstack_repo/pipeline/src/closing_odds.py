from __future__ import annotations

import re

import numpy as np
import pandas as pd

TEAM_FIX = {
    "ARZ": "ARI", "AZ": "ARI", "ARI": "ARI",
    "ATL": "ATL", "BAL": "BAL", "BOS": "BOS", "CHC": "CHC",
    "CWS": "CHW", "CHW": "CHW", "CHA": "CHW",
    "CIN": "CIN", "CLE": "CLE", "COL": "COL", "DET": "DET", "HOU": "HOU",
    "KC": "KCR", "KAN": "KCR", "KCR": "KCR",
    "LAA": "LAA", "ANA": "LAA", "LA": "LAD", "LAD": "LAD",
    "MIA": "MIA", "FLA": "MIA", "MIL": "MIL", "MIN": "MIN",
    "NYM": "NYM", "NYY": "NYY", "PHI": "PHI", "PIT": "PIT",
    "SD": "SDP", "SDP": "SDP", "SEA": "SEA",
    "SF": "SFG", "SFO": "SFG", "SFG": "SFG",
    "STL": "STL", "TB": "TBR", "TAM": "TBR", "TBR": "TBR",
    "TEX": "TEX", "TOR": "TOR", "WSH": "WSN", "WAS": "WSN", "WSN": "WSN",
}


def norm_team(team: object, season: int | None = None) -> str | float:
    """Normalize team abbreviations without retroactively remapping OAK to ATH."""
    if pd.isna(team):
        return np.nan

    value = str(team).strip().upper()
    value = re.sub(r"\s+", " ", value)

    if value == "OAK":
        return "ATH" if season is not None and int(season) >= 2025 else "OAK"
    if value == "ATH":
        return "ATH" if season is None or int(season) >= 2025 else "OAK"

    return TEAM_FIX.get(value, value)


def normalize_team_series(team: pd.Series, season: pd.Series | None = None) -> pd.Series:
    if season is None:
        return team.map(norm_team)
    return pd.Series((norm_team(t, s) for t, s in zip(team, season)), index=team.index, dtype="object")


def american_to_decimal(price: pd.Series | float | int) -> pd.Series | float:
    def one(x):
        if pd.isna(x):
            return np.nan
        x = float(x)
        if 1.01 <= x <= 20:
            return x
        if x > 0:
            return 1 + x / 100
        if x < 0:
            return 1 + 100 / abs(x)
        return np.nan

    if isinstance(price, pd.Series):
        return price.map(one)
    return one(price)


def implied_probability(decimal_odds: pd.Series | float | int) -> pd.Series | float:
    def one(x):
        if pd.isna(x) or float(x) <= 1:
            return np.nan
        return 1 / float(x)

    if isinstance(decimal_odds, pd.Series):
        return decimal_odds.map(one)
    return one(decimal_odds)


def add_vectorized_results(df: pd.DataFrame) -> pd.DataFrame:
    """Add result/profit columns without row-wise apply."""
    out = df.copy()
    out["result"] = np.nan

    ml_mask = out["market"].eq("moneyline") & out["team_score"].notna() & out["opponent_score"].notna()
    out.loc[ml_mask, "result"] = np.select(
        [out.loc[ml_mask, "team_score"] > out.loc[ml_mask, "opponent_score"],
         out.loc[ml_mask, "team_score"] < out.loc[ml_mask, "opponent_score"]],
        ["win", "loss"],
        default="push",
    )

    rl_mask = out["market"].eq("runline") & out["team_score"].notna() & out["opponent_score"].notna() & out["line"].notna()
    adjusted = out.loc[rl_mask, "team_score"] + out.loc[rl_mask, "line"]
    out.loc[rl_mask, "result"] = np.select(
        [adjusted > out.loc[rl_mask, "opponent_score"], adjusted < out.loc[rl_mask, "opponent_score"]],
        ["win", "loss"],
        default="push",
    )

    total_mask = out["market"].eq("total") & out["total_runs"].notna() & out["total"].notna()
    selection = out["selection"].astype(str).str.lower()

    over_mask = total_mask & selection.str.contains("over", na=False)
    out.loc[over_mask, "result"] = np.select(
        [out.loc[over_mask, "total_runs"] > out.loc[over_mask, "total"],
         out.loc[over_mask, "total_runs"] < out.loc[over_mask, "total"]],
        ["win", "loss"],
        default="push",
    )

    under_mask = total_mask & selection.str.contains("under", na=False)
    out.loc[under_mask, "result"] = np.select(
        [out.loc[under_mask, "total_runs"] < out.loc[under_mask, "total"],
         out.loc[under_mask, "total_runs"] > out.loc[under_mask, "total"]],
        ["win", "loss"],
        default="push",
    )

    if "closing_price_decimal" not in out.columns:
        out["closing_price_decimal"] = american_to_decimal(out["closing_price_american"])

    out["profit_1u"] = np.nan
    out.loc[out["result"].eq("push"), "profit_1u"] = 0.0
    out.loc[out["result"].eq("loss"), "profit_1u"] = -1.0
    win_mask = out["result"].eq("win")
    out.loc[win_mask, "profit_1u"] = out.loc[win_mask, "closing_price_decimal"] - 1

    out["bet_count"] = out["result"].isin(["win", "loss"]).astype(int)
    out["win_count"] = out["result"].eq("win").astype(int)
    out["loss_count"] = out["result"].eq("loss").astype(int)
    out["push_count"] = out["result"].eq("push").astype(int)
    return out


def build_shifted_ytd_team_features(team_bets: pd.DataFrame) -> pd.DataFrame:
    """Build leakage-safe YTD features by team, market and season.

    Uses cumsum().shift(1), so current-game result is excluded while first-game YTD remains NaN.
    """
    if team_bets.empty:
        return pd.DataFrame()

    df = team_bets.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    if "season" not in df.columns:
        df["season"] = df["game_date"].dt.year

    df = df.sort_values(["season", "team", "market", "game_date"]).reset_index(drop=True)
    rows: list[pd.DataFrame] = []

    for (_team, _market, _season), g in df.groupby(["team", "market", "season"], dropna=False):
        g = g.sort_values("game_date").copy()
        g["profit_ytd"] = g["profit_1u"].cumsum().shift(1)
        g["bets_ytd"] = g["bet_count"].cumsum().shift(1)
        g["wins_ytd"] = g["win_count"].cumsum().shift(1)
        g["losses_ytd"] = g["loss_count"].cumsum().shift(1)
        g["pushes_ytd"] = g["push_count"].cumsum().shift(1)
        g["roi_ytd"] = g["profit_ytd"] / g["bets_ytd"].replace(0, np.nan)
        g["win_rate_ytd"] = g["wins_ytd"] / g["bets_ytd"].replace(0, np.nan)
        rows.append(g)

    out = pd.concat(rows, ignore_index=True)
    key_cols = ["game_date", "season", "team", "opponent", "home_away"]
    value_cols = ["profit_ytd", "bets_ytd", "wins_ytd", "losses_ytd", "pushes_ytd", "roi_ytd", "win_rate_ytd"]

    wide_parts = []
    for market, market_df in out.groupby("market"):
        tmp = market_df[key_cols + value_cols].copy()
        tmp = tmp.rename(columns={col: f"{market}_{col}" for col in value_cols})
        wide_parts.append(tmp)

    if not wide_parts:
        return pd.DataFrame()

    wide = wide_parts[0]
    for part in wide_parts[1:]:
        wide = wide.merge(part, on=key_cols, how="outer")

    return wide.sort_values(["game_date", "team"]).reset_index(drop=True)


def moneyline_overline_audit(odds: pd.DataFrame, lower: float = 0.95, upper: float = 1.20) -> pd.DataFrame:
    """Return games with suspicious paired ML implied probabilities after dedup."""
    if odds.empty:
        return pd.DataFrame(columns=["game_date", "home_team", "away_team", "overline"])

    df = odds.copy()
    if "implied_probability" not in df.columns:
        if "closing_price_decimal" not in df.columns:
            df["closing_price_decimal"] = american_to_decimal(df["closing_price_american"])
        df["implied_probability"] = implied_probability(df["closing_price_decimal"])

    overline = (
        df[df["market"].eq("moneyline")]
        .groupby(["game_date", "home_team", "away_team"], dropna=False)["implied_probability"]
        .sum(min_count=1)
        .reset_index(name="overline")
    )

    return overline[(overline["overline"] < lower) | (overline["overline"] > upper)].reset_index(drop=True)
