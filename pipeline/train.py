from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from app.calibration import MarketDistributionCalibrator, save_calibrator
from app.model import FEATURE_COLUMNS

TARGET = 'total_runs'


def load_dataset(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [col for col in FEATURE_COLUMNS + [TARGET, 'market_total'] if col not in frame.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if 'game_date' in frame.columns:
        frame = frame.sort_values('game_date')
    return frame.reset_index(drop=True)


def train_model(frame: pd.DataFrame) -> tuple[XGBRegressor, MarketDistributionCalibrator, dict]:
    x = frame[FEATURE_COLUMNS]
    y = frame[TARGET]

    tscv = TimeSeriesSplit(n_splits=5)
    fold_metrics: list[dict] = []
    out_of_fold_predictions = pd.Series(index=frame.index, dtype=float)

    for fold, (train_idx, test_idx) in enumerate(tscv.split(x), start=1):
        model = XGBRegressor(
            n_estimators=450,
            max_depth=3,
            learning_rate=0.035,
            subsample=0.85,
            colsample_bytree=0.85,
            objective='reg:squarederror',
            random_state=42,
        )
        model.fit(x.iloc[train_idx], y.iloc[train_idx])
        preds = model.predict(x.iloc[test_idx])
        out_of_fold_predictions.iloc[test_idx] = preds
        fold_metrics.append(
            {
                'fold': fold,
                'mae': float(mean_absolute_error(y.iloc[test_idx], preds)),
                'rmse': float(mean_squared_error(y.iloc[test_idx], preds) ** 0.5),
            }
        )

    valid_calibration = out_of_fold_predictions.notna()
    calibrator = MarketDistributionCalibrator.from_history(
        raw_predictions=out_of_fold_predictions[valid_calibration].to_numpy(),
        market_totals=frame.loc[valid_calibration, 'market_total'].to_numpy(),
        shrinkage_to_market=0.20,
    )

    final_model = XGBRegressor(
        n_estimators=450,
        max_depth=3,
        learning_rate=0.035,
        subsample=0.85,
        colsample_bytree=0.85,
        objective='reg:squarederror',
        random_state=42,
    )
    final_model.fit(x, y)
    metrics = {
        'folds': fold_metrics,
        'mae_avg': float(pd.DataFrame(fold_metrics)['mae'].mean()),
        'rmse_avg': float(pd.DataFrame(fold_metrics)['rmse'].mean()),
        'rows': int(len(frame)),
        'calibration_rows': int(valid_calibration.sum()),
    }
    return final_model, calibrator, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, help='CSV with pre-game features and total_runs target')
    parser.add_argument('--out', default='models/xgb_totals.joblib')
    parser.add_argument('--calibrator-out', default='models/market_calibrator.joblib')
    args = parser.parse_args()

    frame = load_dataset(args.data)
    model, calibrator, metrics = train_model(frame)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    save_calibrator(calibrator, args.calibrator_out)
    print(metrics)


if __name__ == '__main__':
    main()
