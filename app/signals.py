from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from app.db.supabase_admin import get_supabase_admin
from app.schemas import BetSignal


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_signal_payload(signal: BetSignal) -> dict[str, Any]:
    """Convert API signal response into a durable structured event payload."""
    payload = signal.model_dump(mode='json')
    payload['decision_logged_at'] = utc_now_iso()
    payload['signal_version'] = 'v1'
    return payload


def format_signal_message(signal: BetSignal) -> str:
    """Human-readable alert body for Telegram, Slack, email, or logs."""
    return (
        f'MLB TOTALS SIGNAL\n'
        f'Game ID: {signal.game_id}\n'
        f'Decision: {signal.side.value}\n'
        f'Model Total: {signal.model_total}\n'
        f'Raw Model Total: {signal.raw_model_total}\n'
        f'Market Total: {signal.market_total}\n'
        f'Edge Runs: {signal.edge_runs}\n'
        f'Estimated Probability: {signal.estimated_probability}\n'
        f'Break-even Probability: {signal.break_even_probability}\n'
        f'EV: {signal.expected_value}\n'
        f'Stake: {signal.stake}\n'
        f'Confidence: {signal.confidence}\n'
        f'Reason: {signal.reason}'
    )


def log_signal_decision(signal: BetSignal) -> dict[str, Any]:
    """Legacy audit logger.

    Kept for compatibility. New production metrics should use predictions_log
    through log_prediction_decision().
    """
    payload = build_signal_payload(signal)
    row = {
        'game_id': signal.game_id,
        'side': signal.side.value,
        'should_bet': signal.side.value != 'PASS',
        'model_total': signal.model_total,
        'raw_model_total': signal.raw_model_total,
        'market_total': signal.market_total,
        'edge_runs': signal.edge_runs,
        'estimated_probability': signal.estimated_probability,
        'break_even_probability': signal.break_even_probability,
        'expected_value': signal.expected_value,
        'stake': signal.stake,
        'confidence': signal.confidence,
        'reason': signal.reason,
        'calibration': signal.calibration.model_dump(mode='json'),
        'payload': payload,
        'created_at': payload['decision_logged_at'],
    }
    supabase = get_supabase_admin()
    result = supabase.table('signal_decisions').insert(row).execute()
    return {'inserted': True, 'table': 'signal_decisions', 'data': result.data}


def log_prediction_decision(
    *,
    signal: BetSignal,
    request_received_at: str,
    response_sent_at: str,
    latency_ms: int,
    market_snapshot: dict[str, Any],
    model_version: str = 'unknown',
    feature_version: str = 'v1',
    market_phase: str = 'unknown',
    feature_timestamp: str | None = None,
    features: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist the canonical production prediction log.

    This is the primary table for CLV, ROI, latency, data freshness and leakage
    audits. market_snapshot must be the latest snapshot available at prediction
    time, never a future snapshot.
    """
    payload = build_signal_payload(signal)
    row = {
        'game_id': signal.game_id,
        'model_version': model_version,
        'feature_version': feature_version,
        'prediction_timestamp': request_received_at,
        'request_received_at': request_received_at,
        'response_sent_at': response_sent_at,
        'latency_ms': latency_ms,
        'feature_timestamp': feature_timestamp,
        'market_snapshot_id': market_snapshot.get('id'),
        'market_snapshot_timestamp': market_snapshot['timestamp'],
        'market_phase': market_phase,
        'market_total': signal.market_total,
        'over_price': int(market_snapshot.get('over', -110)),
        'under_price': int(market_snapshot.get('under', -110)),
        'raw_model_total': signal.raw_model_total,
        'calibrated_model_total': signal.model_total,
        'edge_runs': signal.edge_runs,
        'side': signal.side.value,
        'should_bet': signal.side.value != 'PASS',
        'estimated_probability': signal.estimated_probability,
        'break_even_probability': signal.break_even_probability,
        'expected_value': signal.expected_value,
        'stake': signal.stake,
        'confidence': signal.confidence,
        'reason': signal.reason,
        'calibration': signal.calibration.model_dump(mode='json'),
        'features': features or {},
        'payload': payload,
        'truth_status': 'PENDING',
    }
    supabase = get_supabase_admin()
    result = supabase.table('predictions_log').insert(row).execute()
    return {'inserted': True, 'table': 'predictions_log', 'data': result.data}


class LatencyTimer:
    def __init__(self) -> None:
        self.started_at = perf_counter()
        self.request_received_at = utc_now_iso()

    def stop(self) -> tuple[str, int]:
        response_sent_at = utc_now_iso()
        latency_ms = int((perf_counter() - self.started_at) * 1000)
        return response_sent_at, latency_ms
