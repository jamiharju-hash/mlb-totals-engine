import re
import math
from typing import Optional

import numpy as np
import pandas as pd


TEAM_FIX = {
    "ARZ": "ARI", "AZ": "ARI", "ARI": "ARI",
    "CWS": "CHW", "CHW": "CHW", "CHA": "CHW",
    "KC": "KCR", "KAN": "KCR", "KCR": "KCR",
    "LA": "LAD", "LAD": "LAD",
    "SD": "SDP", "SDP": "SDP",
    "SF": "SFG", "SFO": "SFG", "SFG": "SFG",
    "TB": "TBR", "TAM": "TBR", "TBR": "TBR",
    "WSH": "WSN", "WAS": "WSN", "WSN": "WSN",
    "OAK": "ATH", "ATH": "ATH",
}


def snake_case(col: str) -> str:
    col = str(col).strip()
    col = col.replace("%", "pct").replace("+", "plus")
    col = re.sub(r"[^A-Za-z0-9]+", "_", col)
    col = re.sub(r"_+", "_", col)
    return col.strip("_").lower()


def norm_team(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().upper()
    s = re.sub(r"\s+", " ", s)
    return TEAM_FIX.get(s, s)


def safe_numeric(s):
    if s is None:
        return pd.Series(dtype=float)
    if not isinstance(s, pd.Series):
        s = pd.Series(s)
    return pd.to_numeric(
        s.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
        .replace({"": np.nan, "nan": np.nan, "None": np.nan, "-": np.nan}),
        errors="coerce",
    )


def american_to_decimal(price):
    if pd.isna(price):
        return np.nan

    price = float(price)

    # Already decimal odds.
    if 1.01 <= price <= 20:
        return price

    if price > 0:
        return 1 + price / 100

    if price < 0:
        return 1 + 100 / abs(price)

    return np.nan


def decimal_to_american(decimal):
    if pd.isna(decimal):
        return np.nan

    decimal = float(decimal)

    if decimal >= 2:
        return round((decimal - 1) * 100)

    if decimal > 1:
        return round(-100 / (decimal - 1))

    return np.nan


def implied_probability_decimal(decimal):
    if pd.isna(decimal) or decimal <= 1:
        return np.nan
    return 1 / decimal


def moneyline_result(team_score, opponent_score):
    if pd.isna(team_score) or pd.isna(opponent_score):
        return np.nan
    return "win" if team_score > opponent_score else "loss"


def spread_result(team_score, opponent_score, spread):
    if pd.isna(team_score) or pd.isna(opponent_score) or pd.isna(spread):
        return np.nan
    adjusted = team_score + spread
    if adjusted > opponent_score:
        return "win"
    if adjusted < opponent_score:
        return "loss"
    return "push"


def total_result(total_runs, total_line, selection):
    if pd.isna(total_runs) or pd.isna(total_line):
        return np.nan

    selection = str(selection).lower()

    if "over" in selection:
        if total_runs > total_line:
            return "win"
        if total_runs < total_line:
            return "loss"
        return "push"

    if "under" in selection:
        if total_runs < total_line:
            return "win"
        if total_runs > total_line:
            return "loss"
        return "push"

    return np.nan


def profit_1u_american(price, result):
    if result == "push":
        return 0.0
    if result == "loss":
        return -1.0
    if result != "win":
        return np.nan

    price = float(price)

    if 1.01 <= price <= 20:
        return price - 1

    if price > 0:
        return price / 100

    if price < 0:
        return 100 / abs(price)

    return np.nan


def fractional_kelly(probability: float, decimal_odds: float, fraction: float = 0.25, max_stake: float = 0.03) -> float:
    if probability is None or decimal_odds is None:
        return 0.0
    if pd.isna(probability) or pd.isna(decimal_odds) or decimal_odds <= 1:
        return 0.0

    b = decimal_odds - 1
    p = probability
    q = 1 - p

    kelly = (b * p - q) / b

    if kelly <= 0:
        return 0.0

    return float(min(kelly * fraction, max_stake))
