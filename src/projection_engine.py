from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from .utils import fractional_kelly


BetSignal = Literal["BET_STRONG", "BET_SMALL", "NO_BET", "FADE"]


def calculate_weather_run_factor(
    temperature_c: float,
    wind_speed_kph: float,
    wind_direction_type: str,
    humidity_pct: float,
    roof_closed: bool = False,
) -> float:
    if roof_closed:
        return 1.00

    factor = 1.00

    if pd.notna(temperature_c):
        if temperature_c >= 27:
            factor += 0.035
        elif temperature_c <= 10:
            factor -= 0.030

    if pd.notna(wind_speed_kph):
        if wind_direction_type == "out_to_center":
            factor += min(wind_speed_kph / 100, 0.08)
        elif wind_direction_type == "in_from_center":
            factor -= min(wind_speed_kph / 120, 0.07)

    if pd.notna(humidity_pct) and humidity_pct >= 75:
        factor += 0.010

    return round(factor, 4)


def calculate_lineup_handedness_score(
    lineup_df: pd.DataFrame,
    batter_splits: pd.DataFrame,
    opposing_pitcher_hand: str,
) -> float:
    if lineup_df.empty or batter_splits.empty:
        return np.nan

    split = batter_splits[
        batter_splits["vs_pitcher_hand"].astype(str).str.upper().eq(str(opposing_pitcher_hand).upper())
    ].copy()

    merged = lineup_df.merge(split, on="player_id", how="left")

    order_weights = {
        1: 1.15,
        2: 1.12,
        3: 1.10,
        4: 1.08,
        5: 1.03,
        6: 1.00,
        7: 0.95,
        8: 0.92,
        9: 0.90,
    }

    merged["order_weight"] = merged["batting_order"].map(order_weights).fillna(1.0)

    fallback = merged["woba"].median()
    score = (
        merged["woba"].fillna(fallback) *
        merged["order_weight"]
    ).sum() / merged["order_weight"].sum()

    return float(score)


def get_bet_signal(edge_pct: float, model_confidence: float, min_edge: float = 0.03) -> BetSignal:
    if pd.isna(edge_pct) or pd.isna(model_confidence):
        return "NO_BET"

    if edge_pct >= 0.06 and model_confidence >= 0.70:
        return "BET_STRONG"

    if edge_pct >= min_edge and model_confidence >= 0.60:
        return "BET_SMALL"

    if edge_pct <= -0.04:
        return "FADE"

    return "NO_BET"


def build_final_probability(row: pd.Series) -> float:
    probability = float(row.get("base_probability", 0.50))

    probability += float(row.get("pitcher_adjustment", 0.0))
    probability += float(row.get("lineup_adjustment", 0.0))
    probability += float(row.get("handedness_adjustment", 0.0))
    probability += float(row.get("weather_adjustment", 0.0))
    probability += float(row.get("bullpen_adjustment", 0.0))
    probability += float(row.get("manual_override", 0.0))

    # Small market anchoring prevents extreme model drift.
    market_probability = row.get("market_probability", np.nan)
    if pd.notna(market_probability):
        probability = 0.85 * probability + 0.15 * float(market_probability)

    return float(np.clip(probability, 0.01, 0.99))


def score_projection_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["final_probability"] = out.apply(build_final_probability, axis=1)
    out["edge_pct"] = out["final_probability"] - out["market_probability"]

    out["bet_signal"] = out.apply(
        lambda r: get_bet_signal(r["edge_pct"], r.get("model_confidence", 0.65)),
        axis=1,
    )

    out["stake_pct_bankroll"] = out.apply(
        lambda r: fractional_kelly(
            probability=r["final_probability"],
            decimal_odds=r.get("decimal_odds", np.nan),
            fraction=0.25,
            max_stake=0.03,
        ),
        axis=1,
    )

    out["stake_units"] = (out["stake_pct_bankroll"] / 0.01).round(2)

    return out
