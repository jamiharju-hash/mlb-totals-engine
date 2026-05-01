from __future__ import annotations

import numpy as np
import pandas as pd

from .projection_engine import score_projection_rows


def make_sample_projections() -> pd.DataFrame:
    rows = [
        {
            "game_id": "2026-ATL-NYM-001",
            "date": "2026-05-02",
            "team": "ATL",
            "opponent": "NYM",
            "home_away": "home",
            "market": "runline",
            "selection": "ATL -1.5",
            "decimal_odds": 2.05,
            "market_probability": 0.488,
            "base_probability": 0.545,
            "pitcher_adjustment": 0.012,
            "lineup_adjustment": 0.006,
            "handedness_adjustment": 0.018,
            "weather_adjustment": 0.004,
            "bullpen_adjustment": -0.003,
            "manual_override": 0.000,
            "manual_override_flag": False,
            "model_confidence": 0.72,
        },
        {
            "game_id": "2026-CIN-STL-001",
            "date": "2026-05-02",
            "team": "CIN",
            "opponent": "STL",
            "home_away": "away",
            "market": "moneyline",
            "selection": "CIN ML",
            "decimal_odds": 2.24,
            "market_probability": 0.446,
            "base_probability": 0.502,
            "pitcher_adjustment": 0.008,
            "lineup_adjustment": 0.004,
            "handedness_adjustment": 0.010,
            "weather_adjustment": 0.000,
            "bullpen_adjustment": 0.005,
            "manual_override": 0.000,
            "manual_override_flag": False,
            "model_confidence": 0.67,
        },
        {
            "game_id": "2026-HOU-TEX-001",
            "date": "2026-05-02",
            "team": "HOU",
            "opponent": "TEX",
            "home_away": "home",
            "market": "total",
            "selection": "Over 8.5",
            "decimal_odds": 1.91,
            "market_probability": 0.524,
            "base_probability": 0.558,
            "pitcher_adjustment": 0.000,
            "lineup_adjustment": 0.012,
            "handedness_adjustment": 0.007,
            "weather_adjustment": 0.018,
            "bullpen_adjustment": 0.006,
            "manual_override": 0.000,
            "manual_override_flag": False,
            "model_confidence": 0.64,
        },
        {
            "game_id": "2026-PHI-BOS-001",
            "date": "2026-05-02",
            "team": "PHI",
            "opponent": "BOS",
            "home_away": "away",
            "market": "runline",
            "selection": "PHI +1.5",
            "decimal_odds": 1.78,
            "market_probability": 0.562,
            "base_probability": 0.500,
            "pitcher_adjustment": -0.014,
            "lineup_adjustment": -0.005,
            "handedness_adjustment": -0.009,
            "weather_adjustment": 0.000,
            "bullpen_adjustment": -0.006,
            "manual_override": 0.000,
            "manual_override_flag": False,
            "model_confidence": 0.69,
        },
        {
            "game_id": "2026-SD-LAD-001",
            "date": "2026-05-02",
            "team": "SDP",
            "opponent": "LAD",
            "home_away": "home",
            "market": "moneyline",
            "selection": "SDP ML",
            "decimal_odds": 2.35,
            "market_probability": 0.426,
            "base_probability": 0.475,
            "pitcher_adjustment": 0.018,
            "lineup_adjustment": 0.000,
            "handedness_adjustment": 0.012,
            "weather_adjustment": 0.000,
            "bullpen_adjustment": 0.004,
            "manual_override": 0.010,
            "manual_override_flag": True,
            "model_confidence": 0.66,
        },
    ]

    return score_projection_rows(pd.DataFrame(rows))


def make_sample_team_market() -> pd.DataFrame:
    rows = [
        {"team": "ATL", "ml_roi_ytd": 0.196, "rl_roi_ytd": 0.457, "ou_roi_ytd": -0.052, "ml_profit_ytd": 6.28, "rl_profit_ytd": 14.63, "ou_profit_ytd": -1.50},
        {"team": "CIN", "ml_roi_ytd": 0.292, "rl_roi_ytd": 0.182, "ou_roi_ytd": 0.104, "ml_profit_ytd": 9.04, "rl_profit_ytd": 5.63, "ou_profit_ytd": 3.10},
        {"team": "TB", "ml_roi_ytd": 0.177, "rl_roi_ytd": 0.237, "ou_roi_ytd": 0.061, "ml_profit_ytd": 5.31, "rl_profit_ytd": 7.12, "ou_profit_ytd": 1.83},
        {"team": "SDP", "ml_roi_ytd": 0.166, "rl_roi_ytd": 0.230, "ou_roi_ytd": -0.018, "ml_profit_ytd": 4.97, "rl_profit_ytd": 6.90, "ou_profit_ytd": -0.54},
        {"team": "COL", "ml_roi_ytd": 0.172, "rl_roi_ytd": 0.202, "ou_roi_ytd": -0.091, "ml_profit_ytd": 5.51, "rl_profit_ytd": 6.46, "ou_profit_ytd": -2.91},
        {"team": "PHI", "ml_roi_ytd": -0.359, "rl_roi_ytd": -0.595, "ou_roi_ytd": 0.011, "ml_profit_ytd": -11.14, "rl_profit_ytd": -18.44, "ou_profit_ytd": 0.33},
        {"team": "NYM", "ml_roi_ytd": -0.436, "rl_roi_ytd": -0.398, "ou_roi_ytd": -0.043, "ml_profit_ytd": -13.51, "rl_profit_ytd": -12.34, "ou_profit_ytd": -1.20},
        {"team": "BOS", "ml_roi_ytd": -0.288, "rl_roi_ytd": -0.354, "ou_roi_ytd": 0.047, "ml_profit_ytd": -8.92, "rl_profit_ytd": -10.98, "ou_profit_ytd": 1.45},
    ]
    df = pd.DataFrame(rows)
    df["value_score"] = 0.50 * df["rl_roi_ytd"] + 0.35 * df["ml_roi_ytd"] + 0.15 * df["ou_roi_ytd"]
    return df.sort_values("value_score", ascending=False)


def make_sample_model_metrics() -> dict:
    return {
        "as_of": "2026-05-02T08:00:00Z",
        "model_version": "tabular_nn_v0.1",
        "test_mae_start_score": 7.82,
        "test_auc_runline": 0.574,
        "test_auc_moneyline": 0.589,
        "simulated_roi_last_250": 0.071,
        "avg_clv_last_250": 0.018,
        "notes": "Demo metrics. Replace with real training output.",
    }
