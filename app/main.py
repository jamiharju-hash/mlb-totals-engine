from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.calibration import load_calibrator
from app.config import get_settings
from app.ev import build_signal
from app.model import TotalsModel
from app.schemas import BetSignal, CalibrationDetails, PredictionRequest
from app.signals import log_signal_decision

settings = get_settings()
model = TotalsModel(settings.model_path)
calibrator = load_calibrator(settings.calibrator_path)


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
    return {
        'status': 'ok',
        'model_loaded': model.is_loaded,
        'calibrator_loaded': True,
    }


@app.post('/predict', response_model=BetSignal)
def predict(request: PredictionRequest) -> BetSignal:
    features = request.features
    raw_model_total = model.predict(features)
    calibration = calibrator.calibrate(raw_model_total, features.market_total)
    calibrated_total = calibration.calibrated_total

    signal = build_signal(
        game_id=features.game_id,
        model_total=calibrated_total,
        market_total=features.market_total,
        over_price=features.over_price,
        under_price=features.under_price,
        edge_threshold_runs=settings.edge_threshold_runs,
        min_ev=settings.min_ev,
        bankroll=settings.bankroll,
        kelly_fraction=settings.kelly_fraction,
        max_stake_pct=settings.max_stake_pct,
    )
    response = BetSignal(
        game_id=features.game_id,
        side=signal.side,
        model_total=round(calibrated_total, 3),
        raw_model_total=round(raw_model_total, 3),
        market_total=features.market_total,
        edge_runs=signal.edge_runs,
        estimated_probability=signal.estimated_probability,
        break_even_probability=signal.break_even_probability,
        expected_value=signal.expected_value,
        stake=signal.stake,
        confidence=signal.confidence,
        reason=signal.reason,
        calibration=CalibrationDetails(
            raw_total=calibration.raw_total,
            calibrated_total=calibration.calibrated_total,
            residual_vs_market=calibration.residual_vs_market,
            market_percentile=calibration.market_percentile,
            model_percentile=calibration.model_percentile,
            calibration_method=calibration.calibration_method,
        ),
    )
    if request.log_decision:
        log_signal_decision(response)
        response.decision_logged = True
    return response
