from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np


@dataclass(frozen=True)
class CalibrationResult:
    raw_total: float
    calibrated_total: float
    market_total: float
    residual_vs_market: float
    market_percentile: float
    model_percentile: float
    calibration_method: str


@dataclass(frozen=True)
class MarketDistributionCalibrator:
    """Calibrate model totals to the observed market distribution.

    The model predicts a continuous total-runs number. This layer prevents the
    model from drifting into an unrealistic output distribution by mapping the
    raw prediction percentile into the empirical closing-market distribution.
    """

    model_quantiles: np.ndarray
    market_quantiles: np.ndarray
    shrinkage_to_market: float = 0.20

    @classmethod
    def identity(cls) -> MarketDistributionCalibrator:
        quantiles = np.linspace(5.0, 13.0, 101)
        return cls(model_quantiles=quantiles, market_quantiles=quantiles, shrinkage_to_market=0.20)

    @classmethod
    def from_history(
        cls,
        raw_predictions: np.ndarray,
        market_totals: np.ndarray,
        shrinkage_to_market: float = 0.20,
    ) -> MarketDistributionCalibrator:
        if len(raw_predictions) < 50 or len(market_totals) < 50:
            raise ValueError('At least 50 historical observations are required for calibration')
        probabilities = np.linspace(0.0, 1.0, 101)
        model_quantiles = np.quantile(raw_predictions, probabilities)
        market_quantiles = np.quantile(market_totals, probabilities)
        return cls(
            model_quantiles=model_quantiles,
            market_quantiles=market_quantiles,
            shrinkage_to_market=shrinkage_to_market,
        )

    def calibrate(self, raw_total: float, market_total: float) -> CalibrationResult:
        model_percentile = float(np.interp(raw_total, self.model_quantiles, np.linspace(0.0, 1.0, len(self.model_quantiles))))
        distribution_matched_total = float(
            np.interp(model_percentile, np.linspace(0.0, 1.0, len(self.market_quantiles)), self.market_quantiles)
        )
        calibrated_total = (
            distribution_matched_total * (1.0 - self.shrinkage_to_market)
            + float(market_total) * self.shrinkage_to_market
        )
        market_percentile = float(
            np.interp(float(market_total), self.market_quantiles, np.linspace(0.0, 1.0, len(self.market_quantiles)))
        )
        return CalibrationResult(
            raw_total=round(float(raw_total), 4),
            calibrated_total=round(calibrated_total, 4),
            market_total=round(float(market_total), 4),
            residual_vs_market=round(calibrated_total - float(market_total), 4),
            market_percentile=round(market_percentile, 4),
            model_percentile=round(model_percentile, 4),
            calibration_method='empirical_quantile_market_distribution',
        )


def load_calibrator(path: str | Path | None) -> MarketDistributionCalibrator:
    if path is None:
        return MarketDistributionCalibrator.identity()
    calibration_path = Path(path)
    if not calibration_path.exists():
        return MarketDistributionCalibrator.identity()
    loaded: Any = joblib.load(calibration_path)
    if not isinstance(loaded, MarketDistributionCalibrator):
        raise TypeError(f'Invalid calibrator artifact: {calibration_path}')
    return loaded


def save_calibrator(calibrator: MarketDistributionCalibrator, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibrator, output)
