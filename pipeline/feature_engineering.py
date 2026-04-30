from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureConfig:
    league_avg_era: float = 4.20
    league_avg_ops: float = 0.720
    league_avg_wrc_plus: float = 100.0
    league_avg_bullpen_pitches_3d: float = 120.0
    default_park_factor: float = 1.0
    default_temperature_f: float = 70.0
    default_wind_out_mph: float = 0.0


MODEL_FEATURE_COLUMNS = [
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
    'pitching_strength_diff',
    'offensive_efficiency_diff',
    'bullpen_fatigue_diff',
    'lineup_strength_diff',
    'park_weather_run_adjustment',
    'market_total_zscore',
    'market_line_move',
    'market_overround',
]


def american_implied_probability(price: float | int | None) -> float | None:
    if price is None or pd.isna(price) or price == 0:
        return None
    price = float(price)
    if price > 0:
        return 100 / (price + 100)
    return abs(price) / (abs(price) + 100)


def no_vig_probabilities(over_price: float | int | None, under_price: float | int | None) -> tuple[float | None, float | None, float | None]:
    over_prob = american_implied_probability(over_price)
    under_prob = american_implied_probability(under_price)
    if over_prob is None or under_prob is None:
        return None, None, None
    overround = over_prob + under_prob
    if overround <= 0:
        return None, None, None
    return over_prob / overround, under_prob / overround, overround - 1


def pitching_strength_differential(row: Mapping[str, Any], config: FeatureConfig = FeatureConfig()) -> float:
    home_era = float(row.get('home_sp_era') or config.league_avg_era)
    away_era = float(row.get('away_sp_era') or config.league_avg_era)
    home_kbb = float(row.get('home_sp_kbb') or 2.7)
    away_kbb = float(row.get('away_sp_kbb') or 2.7)

    home_strength = (config.league_avg_era - home_era) + (home_kbb - 2.7) * 0.35
    away_strength = (config.league_avg_era - away_era) + (away_kbb - 2.7) * 0.35
    return round(home_strength - away_strength, 5)


def offensive_efficiency_metrics(row: Mapping[str, Any], config: FeatureConfig = FeatureConfig()) -> tuple[float, float, float]:
    home_ops = float(row.get('home_ops_14d') or config.league_avg_ops)
    away_ops = float(row.get('away_ops_14d') or config.league_avg_ops)
    home_wrc = float(row.get('home_wrc_plus_14d') or config.league_avg_wrc_plus)
    away_wrc = float(row.get('away_wrc_plus_14d') or config.league_avg_wrc_plus)

    home_efficiency = ((home_ops / config.league_avg_ops) - 1) + ((home_wrc / 100) - 1)
    away_efficiency = ((away_ops / config.league_avg_ops) - 1) + ((away_wrc / 100) - 1)
    return round(home_efficiency, 5), round(away_efficiency, 5), round(home_efficiency - away_efficiency, 5)


def bullpen_fatigue_model(row: Mapping[str, Any], config: FeatureConfig = FeatureConfig()) -> tuple[float, float, float]:
    home_pitches_3d = float(row.get('home_bullpen_pitches_3d') or config.league_avg_bullpen_pitches_3d)
    away_pitches_3d = float(row.get('away_bullpen_pitches_3d') or config.league_avg_bullpen_pitches_3d)
    home_back_to_back = float(row.get('home_relievers_back_to_back') or 0)
    away_back_to_back = float(row.get('away_relievers_back_to_back') or 0)

    home_fatigue = (home_pitches_3d / config.league_avg_bullpen_pitches_3d) + home_back_to_back * 0.12
    away_fatigue = (away_pitches_3d / config.league_avg_bullpen_pitches_3d) + away_back_to_back * 0.12
    return round(home_fatigue, 5), round(away_fatigue, 5), round(home_fatigue - away_fatigue, 5)


def lineup_strength(row: Mapping[str, Any]) -> tuple[float, float, float]:
    home_confirmed = 1.0 if row.get('home_lineup_confirmed') else 0.0
    away_confirmed = 1.0 if row.get('away_lineup_confirmed') else 0.0
    home_projected_woba = float(row.get('home_lineup_projected_woba') or 0.315)
    away_projected_woba = float(row.get('away_lineup_projected_woba') or 0.315)
    home_missing_starters = float(row.get('home_missing_regular_starters') or 0)
    away_missing_starters = float(row.get('away_missing_regular_starters') or 0)

    home_strength = home_projected_woba + home_confirmed * 0.01 - home_missing_starters * 0.008
    away_strength = away_projected_woba + away_confirmed * 0.01 - away_missing_starters * 0.008
    return round(home_strength, 5), round(away_strength, 5), round(home_strength - away_strength, 5)


def park_weather_adjustment(row: Mapping[str, Any], config: FeatureConfig = FeatureConfig()) -> float:
    park_factor = float(row.get('park_factor') or config.default_park_factor)
    temperature_f = float(row.get('temperature_f') or config.default_temperature_f)
    wind_out_mph = float(row.get('wind_out_mph') or config.default_wind_out_mph)
    roof_closed = bool(row.get('roof_closed', False))

    if roof_closed:
        temperature_delta = 0.0
        wind_delta = 0.0
    else:
        temperature_delta = (temperature_f - 70.0) * 0.012
        wind_delta = wind_out_mph * 0.035

    park_delta = (park_factor - 1.0) * 1.75
    return round(park_delta + temperature_delta + wind_delta, 5)


def market_line_embedding(row: Mapping[str, Any], market_mean: float = 8.6, market_std: float = 1.15) -> tuple[float, float, float]:
    market_total = float(row.get('market_total'))
    opening_total = row.get('opening_total')
    market_line_move = 0.0 if opening_total is None or pd.isna(opening_total) else market_total - float(opening_total)
    _, _, overround = no_vig_probabilities(row.get('over_price'), row.get('under_price'))
    market_total_zscore = (market_total - market_mean) / market_std if market_std > 0 else 0.0
    return round(market_total_zscore, 5), round(market_line_move, 5), round(overround or 0.0, 5)


def build_game_feature_row(row: Mapping[str, Any], config: FeatureConfig = FeatureConfig()) -> dict[str, Any]:
    home_off, away_off, off_diff = offensive_efficiency_metrics(row, config)
    home_fatigue, away_fatigue, fatigue_diff = bullpen_fatigue_model(row, config)
    home_lineup, away_lineup, lineup_diff = lineup_strength(row)
    market_z, line_move, overround = market_line_embedding(row)

    return {
        'game_id': row.get('game_id'),
        'game_date': row.get('game_date'),
        'market_total': float(row.get('market_total')),
        'home_sp_era': float(row.get('home_sp_era') or config.league_avg_era),
        'away_sp_era': float(row.get('away_sp_era') or config.league_avg_era),
        'home_bullpen_era_7d': float(row.get('home_bullpen_era_7d') or config.league_avg_era),
        'away_bullpen_era_7d': float(row.get('away_bullpen_era_7d') or config.league_avg_era),
        'home_ops_14d': float(row.get('home_ops_14d') or config.league_avg_ops),
        'away_ops_14d': float(row.get('away_ops_14d') or config.league_avg_ops),
        'park_factor': float(row.get('park_factor') or config.default_park_factor),
        'temperature_f': float(row.get('temperature_f') or config.default_temperature_f),
        'wind_out_mph': float(row.get('wind_out_mph') or config.default_wind_out_mph),
        'pitching_strength_diff': pitching_strength_differential(row, config),
        'home_offensive_efficiency': home_off,
        'away_offensive_efficiency': away_off,
        'offensive_efficiency_diff': off_diff,
        'home_bullpen_fatigue': home_fatigue,
        'away_bullpen_fatigue': away_fatigue,
        'bullpen_fatigue_diff': fatigue_diff,
        'home_lineup_strength': home_lineup,
        'away_lineup_strength': away_lineup,
        'lineup_strength_diff': lineup_diff,
        'park_weather_run_adjustment': park_weather_adjustment(row, config),
        'market_total_zscore': market_z,
        'market_line_move': line_move,
        'market_overround': overround,
        'over_price': int(row.get('over_price') or -110),
        'under_price': int(row.get('under_price') or -110),
        'total_runs': row.get('total_runs'),
    }


def build_feature_frame(raw_frame: pd.DataFrame, config: FeatureConfig = FeatureConfig()) -> pd.DataFrame:
    if raw_frame.empty:
        return pd.DataFrame()
    required = {'game_id', 'market_total'}
    missing = required - set(raw_frame.columns)
    if missing:
        raise ValueError(f'Missing required raw feature columns: {sorted(missing)}')

    features = pd.DataFrame([build_game_feature_row(row, config) for row in raw_frame.to_dict(orient='records')])
    numeric_columns = [col for col in features.columns if col not in {'game_id', 'game_date'}]
    for col in numeric_columns:
        features[col] = pd.to_numeric(features[col], errors='ignore')
    features = features.replace([np.inf, -np.inf], np.nan)
    return features
