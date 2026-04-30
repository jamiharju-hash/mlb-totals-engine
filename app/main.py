from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.ev import build_signal
from app.model import TotalsModel
from app.schemas import BetSignal, PredictionRequest

settings = get_settings()
model = TotalsModel(settings.model_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model.load()
    yield


app = FastAPI(
    title='MLB Totals Engine',
    version='0.1.0',
    description='Closed-loop MLB totals betting intelligence API.',
    lifespan=lifespan,
)


@app.get('/health')
def health() -> dict:
    return {'status': 'ok', 'model_loaded': model.is_loaded}


@app.post('/predict', response_model=BetSignal)
def predict(request: PredictionRequest) -> BetSignal:
    features = request.features
    model_total = model.predict(features)
    signal = build_signal(
        game_id=features.game_id,
        model_total=model_total,
        market_total=features.market_total,
        over_price=features.over_price,
        under_price=features.under_price,
        edge_threshold_runs=settings.edge_threshold_runs,
        min_ev=settings.min_ev,
        bankroll=settings.bankroll,
        kelly_fraction=settings.kelly_fraction,
        max_stake_pct=settings.max_stake_pct,
    )
    return BetSignal(
        game_id=features.game_id,
        side=signal.side,
        model_total=round(model_total, 3),
        market_total=features.market_total,
        edge_runs=signal.edge_runs,
        estimated_probability=signal.estimated_probability,
        break_even_probability=signal.break_even_probability,
        expected_value=signal.expected_value,
        stake=signal.stake,
        confidence=signal.confidence,
        reason=signal.reason,
    )
