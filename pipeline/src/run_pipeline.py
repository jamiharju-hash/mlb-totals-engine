from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import FEATURE_DIR, DASHBOARD_OUTPUT
from .sample_data import make_sample_projections, make_sample_team_market, make_sample_model_metrics


def dataframe_to_records(df: pd.DataFrame):
    clean = df.copy()

    for c in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[c]):
            clean[c] = clean[c].dt.strftime("%Y-%m-%d")

    clean = clean.replace({np.nan: None})
    return clean.to_dict(orient="records")


def load_or_sample(path: Path, sample_func):
    if path.exists():
        return pd.read_parquet(path)
    return sample_func()


def build_dashboard_payload() -> dict:
    projections_path = FEATURE_DIR / "projections_today.parquet"
    team_market_path = FEATURE_DIR / "team_market_value_daily_latest.parquet"
    metrics_path = FEATURE_DIR / "model_metrics.json"

    projections = load_or_sample(projections_path, make_sample_projections)
    team_market = load_or_sample(team_market_path, make_sample_team_market)

    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
    else:
        metrics = make_sample_model_metrics()

    # Save sample parquet outputs if real files do not exist yet.
    projections.to_parquet(projections_path, index=False)
    team_market.to_parquet(team_market_path, index=False)
    metrics_path.write_text(json.dumps(metrics, indent=2))

    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "summary": {
            "projection_count": int(len(projections)),
            "bet_count": int(projections["bet_signal"].isin(["BET_SMALL", "BET_STRONG"]).sum()),
            "strong_bet_count": int((projections["bet_signal"] == "BET_STRONG").sum()),
            "average_edge_pct": float(projections["edge_pct"].mean()),
            "max_edge_pct": float(projections["edge_pct"].max()),
            "teams_tracked": int(team_market["team"].nunique()),
        },
        "projections": dataframe_to_records(projections),
        "team_market": dataframe_to_records(team_market),
        "model_metrics": metrics,
    }

    return payload


def main():
    payload = build_dashboard_payload()
    DASHBOARD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_OUTPUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote dashboard JSON: {DASHBOARD_OUTPUT}")


if __name__ == "__main__":
    main()
