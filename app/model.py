from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.schemas import GameFeatures


FEATURE_COLUMNS = [
    'market_total',
    'home_sp_era',
    'away_sp_era',
    'home_bullpen_era_7d',
    'away_bullpen_era_7d',
    'home_ops_14d',
    'away_ops_14d',
    'park_factor',
    'temperature_f',
    'wind_out_mph',
]

DEFAULTS = {
    'home_sp_era': 4.20,
    'away_sp_era': 4.20,
    'home_bullpen_era_7d': 4.10,
    'away_bullpen_era_7d': 4.10,
    'home_ops_14d': 0.720,
    'away_ops_14d': 0.720,
    'park_factor': 1.00,
    'temperature_f': 70.0,
    'wind_out_mph': 0.0,
}


class TotalsModel:
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self._model: Any | None = None

    def load(self) -> None:
        if self.model_path.exists():
            self._model = joblib.load(self.model_path)

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def predict(self, features: GameFeatures) -> float:
        row = features.model_dump()
        for key, default in DEFAULTS.items():
            if row.get(key) is None:
                row[key] = default
        frame = pd.DataFrame([{col: row[col] for col in FEATURE_COLUMNS}])

        if self._model is not None:
            return float(self._model.predict(frame)[0])

        # Deterministic fallback before first training run.
        # Keeps API usable but deliberately anchored to market total.
        pitcher_delta = (row['home_sp_era'] + row['away_sp_era'] - 8.4) * 0.18
        bullpen_delta = (row['home_bullpen_era_7d'] + row['away_bullpen_era_7d'] - 8.2) * 0.12
        offense_delta = (row['home_ops_14d'] + row['away_ops_14d'] - 1.44) * 2.5
        park_delta = (row['park_factor'] - 1.0) * 1.6
        weather_delta = ((row['temperature_f'] - 70.0) * 0.01) + (row['wind_out_mph'] * 0.035)
        prediction = row['market_total'] + pitcher_delta + bullpen_delta + offense_delta + park_delta + weather_delta
        return float(np.clip(prediction, 4.0, 15.0))
