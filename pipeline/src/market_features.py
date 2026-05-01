import numpy as np
import pandas as pd


def build_team_market_rows(bets: pd.DataFrame) -> pd.DataFrame:
    rows = []

    team_side = bets[bets["market"].isin(["moneyline", "runline"]) & bets["team"].notna()].copy()
    if not team_side.empty:
        rows.append(team_side)

    totals = bets[bets["market"].eq("total")].copy()
    if not totals.empty:
        home = totals.copy()
        home["team"] = home["home_team"]
        home["opponent"] = home["away_team"]
        home["home_away"] = "home"

        away = totals.copy()
        away["team"] = away["away_team"]
        away["opponent"] = away["home_team"]
        away["home_away"] = "away"

        rows.extend([home, away])

    if not rows:
        return pd.DataFrame()

    out = pd.concat(rows, ignore_index=True, sort=False)
    return out.dropna(subset=["team"])


def build_shifted_ytd_team_features(team_bets: pd.DataFrame) -> pd.DataFrame:
    if team_bets.empty:
        return pd.DataFrame()

    df = team_bets.copy()
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(["team", "market", "game_date"]).reset_index(drop=True)

    rows = []

    for (team, market), g in df.groupby(["team", "market"], dropna=False):
        g = g.sort_values("game_date").copy()

        g["profit_ytd"] = g["profit_1u"].shift(1).cumsum()
        g["bets_ytd"] = g["bet_count"].shift(1).cumsum()
        g["wins_ytd"] = g["win_count"].shift(1).cumsum()
        g["losses_ytd"] = g["loss_count"].shift(1).cumsum()
        g["pushes_ytd"] = g["push_count"].shift(1).cumsum()

        g["roi_ytd"] = g["profit_ytd"] / g["bets_ytd"].replace(0, np.nan)
        g["win_rate_ytd"] = g["wins_ytd"] / g["bets_ytd"].replace(0, np.nan)

        rows.append(g)

    out = pd.concat(rows, ignore_index=True)

    key_cols = ["game_date", "season", "team", "opponent", "home_away"]
    value_cols = ["profit_ytd", "bets_ytd", "wins_ytd", "losses_ytd", "pushes_ytd", "roi_ytd", "win_rate_ytd"]

    wide_parts = []
    for market, g in out.groupby("market"):
        tmp = g[key_cols + value_cols].copy()
        tmp = tmp.rename(columns={c: f"{market}_{c}" for c in value_cols})
        wide_parts.append(tmp)

    if not wide_parts:
        return pd.DataFrame()

    wide = wide_parts[0]
    for part in wide_parts[1:]:
        wide = wide.merge(part, on=key_cols, how="outer")

    return wide.sort_values(["game_date", "team"]).reset_index(drop=True)
