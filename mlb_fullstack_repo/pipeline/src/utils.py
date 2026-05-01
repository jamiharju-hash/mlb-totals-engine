import numpy as np
import pandas as pd

def fractional_kelly(probability: float, decimal_odds: float, fraction: float = 0.25, max_stake: float = 0.03) -> float:
    if pd.isna(probability) or pd.isna(decimal_odds) or decimal_odds <= 1:
        return 0.0
    b = decimal_odds - 1
    p = probability
    q = 1 - p
    kelly = (b * p - q) / b
    if kelly <= 0:
        return 0.0
    return float(min(kelly * fraction, max_stake))

def get_bet_signal(edge_pct, model_confidence, min_edge=0.03):
    if pd.isna(edge_pct) or pd.isna(model_confidence):
        return "NO_BET"
    if edge_pct >= 0.06 and model_confidence >= 0.70:
        return "BET_STRONG"
    if edge_pct >= min_edge and model_confidence >= 0.60:
        return "BET_SMALL"
    if edge_pct <= -0.04:
        return "FADE"
    return "NO_BET"
