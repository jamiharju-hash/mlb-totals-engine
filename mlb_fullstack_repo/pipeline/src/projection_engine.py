import numpy as np
import pandas as pd
from .utils import fractional_kelly, get_bet_signal

def build_final_probability(row):
    p = float(row.get("base_probability", 0.50))
    for col in ["pitcher_adjustment", "lineup_adjustment", "handedness_adjustment", "weather_adjustment", "bullpen_adjustment", "manual_override"]:
        p += float(row.get(col, 0.0))
    market_probability = row.get("market_probability", np.nan)
    if pd.notna(market_probability):
        p = 0.85 * p + 0.15 * float(market_probability)
    return float(np.clip(p, 0.01, 0.99))

def score_projection_rows(df):
    out = df.copy()
    out["final_probability"] = out.apply(build_final_probability, axis=1)
    out["edge_pct"] = out["final_probability"] - out["market_probability"]
    out["bet_signal"] = out.apply(lambda r: get_bet_signal(r["edge_pct"], r.get("model_confidence", 0.65)), axis=1)
    out["stake_pct_bankroll"] = out.apply(lambda r: fractional_kelly(r["final_probability"], r["decimal_odds"]), axis=1)
    out["stake_units"] = (out["stake_pct_bankroll"] / 0.01).round(2)
    return out
