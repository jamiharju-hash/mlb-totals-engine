from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.calibration import load_calibrator
from app.config import get_settings
from app.db.supabase_admin import get_supabase_admin
from app.ev import build_signal
from app.model import TotalsModel
from app.schemas import BetSignal, CalibrationDetails, PredictionRequest
from app.signals import LatencyTimer, log_prediction_decision
from app.truth_layer import get_latest_market_snapshot_before_prediction

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


@app.get('/metrics')
def metrics() -> dict:
    """Return canonical dashboard metrics from READY predictions only."""
    supabase = get_supabase_admin()
    summary = supabase.table('metrics_summary').select('*').single().execute()
    buckets = supabase.table('edge_bucket_analysis').select('*').execute()
    data = summary.data or {}
    return {
        'roi': data.get('roi', 0),
        'clv': data.get('avg_clv', 0),
        'clv_win_rate': data.get('clv_win_rate', 0),
        'bet_count': data.get('bet_count', 0),
        'win_rate': data.get('win_rate', 0),
        'total_staked': data.get('total_staked', 0),
        'pnl': data.get('pnl', 0),
        'avg_latency_ms': data.get('avg_latency_ms', 0),
        'data_lag_seconds': data.get('data_lag_seconds', 0),
        'edge_buckets': buckets.data or [],
    }


@app.post('/predict', response_model=BetSignal)
def predict(request: PredictionRequest) -> BetSignal:
    timer = LatencyTimer()
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
        response_sent_at, latency_ms = timer.stop()
        market_snapshot = get_latest_market_snapshot_before_prediction(
            features.game_id,
            timer.request_received_at,
        ) or {
            'id': None,
            'timestamp': timer.request_received_at,
            'line': features.market_total,
            'over': features.over_price,
            'under': features.under_price,
        }
        log_prediction_decision(
            signal=response,
            request_received_at=timer.request_received_at,
            response_sent_at=response_sent_at,
            latency_ms=latency_ms,
            market_snapshot=market_snapshot,
            features=features.model_dump(mode='json'),
        )
        response.decision_logged = True
    return response
