import pandas as pd
from .projection_engine import score_projection_rows

def make_sample_payload():
    projections = pd.DataFrame([
        {
            "game_id": "2026-ATL-NYM-001", "game_date": "2026-05-02", "team": "ATL", "opponent": "NYM", "home_away": "home",
            "market": "runline", "selection": "ATL -1.5", "decimal_odds": 2.05, "american_odds": 105,
            "market_probability": 0.488, "base_probability": 0.545,
            "pitcher_adjustment": 0.012, "lineup_adjustment": 0.006, "handedness_adjustment": 0.018,
            "weather_adjustment": 0.004, "bullpen_adjustment": -0.003, "manual_override": 0.0,
            "manual_override_flag": False, "model_confidence": 0.72
        },
        {
            "game_id": "2026-CIN-STL-001", "game_date": "2026-05-02", "team": "CIN", "opponent": "STL", "home_away": "away",
            "market": "moneyline", "selection": "CIN ML", "decimal_odds": 2.24, "american_odds": 124,
            "market_probability": 0.446, "base_probability": 0.502,
            "pitcher_adjustment": 0.008, "lineup_adjustment": 0.004, "handedness_adjustment": 0.010,
            "weather_adjustment": 0.0, "bullpen_adjustment": 0.005, "manual_override": 0.0,
            "manual_override_flag": False, "model_confidence": 0.67
        }
    ])
    projections = score_projection_rows(projections)

    team_market = pd.DataFrame([
        {"as_of_date": "2026-05-02", "team": "ATL", "ml_roi_ytd": 0.196, "rl_roi_ytd": 0.457, "ou_roi_ytd": -0.052, "ml_profit_ytd": 6.28, "rl_profit_ytd": 14.63, "ou_profit_ytd": -1.50},
        {"as_of_date": "2026-05-02", "team": "CIN", "ml_roi_ytd": 0.292, "rl_roi_ytd": 0.182, "ou_roi_ytd": 0.104, "ml_profit_ytd": 9.04, "rl_profit_ytd": 5.63, "ou_profit_ytd": 3.10}
    ])
    team_market["value_score"] = 0.50 * team_market["rl_roi_ytd"] + 0.35 * team_market["ml_roi_ytd"] + 0.15 * team_market["ou_roi_ytd"]

    metrics = {
        "as_of": "2026-05-02T08:00:00Z",
        "model_version": "free_stack_demo_v0.1",
        "test_mae_start_score": 7.82,
        "test_auc_runline": 0.574,
        "test_auc_moneyline": 0.589,
        "simulated_roi_last_250": 0.071,
        "avg_clv_last_250": 0.018,
        "notes": "Demo metrics. Replace with real training output."
    }

    return {
        "projections": projections.where(pd.notna(projections), None).to_dict(orient="records"),
        "team_market": team_market.where(pd.notna(team_market), None).to_dict(orient="records"),
        "model_metrics": metrics
    }
