from __future__ import annotations

from datetime import datetime, timezone
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
    """Persist one model decision to Supabase.

    Uses service-role Supabase admin client, so this must only run backend-side.
    Logs both bet and no-bet decisions for auditability and calibration analysis.
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
    return {'inserted': True, 'result': result.model_dump() if hasattr(result, 'model_dump') else str(result)}
