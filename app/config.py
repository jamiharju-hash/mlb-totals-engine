from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    environment: str = 'local'
    log_level: str = 'INFO'

    mlb_stats_api_base_url: str = 'https://statsapi.mlb.com/api/v1'
    odds_api_base_url: str = 'https://api.the-odds-api.com/v4'
    odds_api_key: str | None = None
    odds_regions: str = 'us'
    odds_markets: str = 'totals'
    odds_bookmakers: str = 'draftkings,fanduel,betmgm,caesars,pinnacle'

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

    model_path: str = 'models/xgb_totals.joblib'
    calibrator_path: str = 'models/market_calibrator.joblib'
    edge_threshold_runs: float = 0.25
    min_ev: float = 0.015
    kelly_fraction: float = 0.25
    bankroll: float = 10_000
    max_stake_pct: float = 0.02


@lru_cache
def get_settings() -> Settings:
    return Settings()
