from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class BetSide(StrEnum):
    over = 'OVER'
    under = 'UNDER'
    pass_bet = 'PASS'


class GameFeatures(BaseModel):
    game_id: str
    game_datetime: datetime | None = None
    home_team: str
    away_team: str
    market_total: float = Field(gt=0)
    over_price: int = -110
    under_price: int = -110

    home_sp_era: float | None = None
    away_sp_era: float | None = None
    home_bullpen_era_7d: float | None = None
    away_bullpen_era_7d: float | None = None
    home_ops_14d: float | None = None
    away_ops_14d: float | None = None
    park_factor: float = 1.0
    temperature_f: float | None = None
    wind_out_mph: float | None = None


class PredictionRequest(BaseModel):
    features: GameFeatures


class BetSignal(BaseModel):
    game_id: str
    side: BetSide
    model_total: float
    market_total: float
    edge_runs: float
    estimated_probability: float
    break_even_probability: float
    expected_value: float
    stake: float
    confidence: str
    reason: str
