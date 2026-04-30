from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from app.model import FEATURE_COLUMNS

TARGET = 'total_runs'


def load_dataset(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [col for col in FEATURE_COLUMNS + [TARGET] if col not in frame.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if 'game_date' in frame.columns:
        frame = frame.sort_values('game_date')
    return frame.reset_index(drop=True)


def train_model(frame: pd.DataFrame) -> tuple[XGBRegressor, dict]:
    x = frame[FEATURE_COLUMNS]
    y = frame[TARGET]

    tscv = TimeSeriesSplit(n_splits=5)
    fold_metrics: list[dict] = []
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
        fold_metrics.append(
            {
                'fold': fold,
                'mae': float(mean_absolute_error(y.iloc[test_idx], preds)),
                'rmse': float(mean_squared_error(y.iloc[test_idx], preds) ** 0.5),
            }
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
    }
    return final_model, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, help='CSV with pre-game features and total_runs target')
    parser.add_argument('--out', default='models/xgb_totals.joblib')
    args = parser.parse_args()

    frame = load_dataset(args.data)
    model, metrics = train_model(frame)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    print(metrics)


if __name__ == '__main__':
    main()
