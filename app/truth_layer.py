from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db.supabase_admin import get_supabase_admin


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def calculate_clv_for_side(side: str, market_total: float, closing_total: float) -> float:
    side = side.upper()
    if side == 'OVER':
        return round(float(closing_total) - float(market_total), 4)
    if side == 'UNDER':
        return round(float(market_total) - float(closing_total), 4)
    return 0.0


def get_latest_market_snapshot_before_prediction(game_id: str, prediction_timestamp: str) -> dict[str, Any] | None:
    """Return the latest odds snapshot known at prediction time.

    This prevents using future line movement as a model input or evaluation baseline.
    """
    supabase = get_supabase_admin()
    result = (
        supabase.table('odds_snapshots')
        .select('*')
        .eq('game_id', game_id)
        .lte('timestamp', prediction_timestamp)
        .order('timestamp', desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def get_closing_snapshot(game_id: str) -> dict[str, Any] | None:
    """Return the latest available market snapshot for a completed game.

    In production, this should be restricted to snapshots before first pitch.
    If first-pitch timestamps are available, add timestamp <= game_datetime.
    """
    supabase = get_supabase_admin()
    result = (
        supabase.table('odds_snapshots')
        .select('*')
        .eq('game_id', game_id)
        .order('timestamp', desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def get_final_result(game_id: str) -> dict[str, Any] | None:
    supabase = get_supabase_admin()
    result = (
        supabase.table('game_results')
        .select('*')
        .eq('game_id', game_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def create_pending_truth_link(signal_decision_id: int, signal_row: dict[str, Any]) -> dict[str, Any]:
    """Create the initial truth link at prediction time.

    Required signal_row fields:
        game_id, created_at, market_total, side
    """
    prediction_timestamp = signal_row.get('prediction_timestamp') or signal_row.get('created_at') or utc_now_iso()
    game_id = signal_row['game_id']
    market_snapshot = get_latest_market_snapshot_before_prediction(game_id, prediction_timestamp)
    if not market_snapshot:
        raise RuntimeError(f'No market snapshot exists before prediction timestamp for game_id={game_id}')

    row = {
        'signal_decision_id': signal_decision_id,
        'game_id': game_id,
        'prediction_timestamp': prediction_timestamp,
        'market_snapshot_id': market_snapshot['id'],
        'market_snapshot_timestamp': market_snapshot['timestamp'],
        'market_total': market_snapshot['line'],
        'market_over': market_snapshot['over'],
        'market_under': market_snapshot['under'],
        'truth_status': 'PENDING',
    }
    supabase = get_supabase_admin()
    result = supabase.table('prediction_truth_links').insert(row).execute()
    return result.data[0]


def finalize_truth_link(signal_decision_id: int, side: str) -> dict[str, Any]:
    """Attach closing line and ground truth to a pending prediction link."""
    supabase = get_supabase_admin()
    link_result = (
        supabase.table('prediction_truth_links')
        .select('*')
        .eq('signal_decision_id', signal_decision_id)
        .limit(1)
        .execute()
    )
    links = link_result.data or []
    if not links:
        raise RuntimeError(f'No prediction_truth_link found for signal_decision_id={signal_decision_id}')

    link = links[0]
    game_id = link['game_id']
    closing_snapshot = get_closing_snapshot(game_id)
    result = get_final_result(game_id)

    if not closing_snapshot or not result:
        return link

    clv = calculate_clv_for_side(side, float(link['market_total']), float(closing_snapshot['line']))
    update = {
        'closing_snapshot_id': closing_snapshot['id'],
        'closing_snapshot_timestamp': closing_snapshot['timestamp'],
        'closing_total': closing_snapshot['line'],
        'closing_over': closing_snapshot['over'],
        'closing_under': closing_snapshot['under'],
        'result_finalized_at': result['finalized_at'],
        'total_runs': result['total_runs'],
        'clv': clv,
        'truth_status': 'READY',
        'updated_at': utc_now_iso(),
    }
    updated = (
        supabase.table('prediction_truth_links')
        .update(update)
        .eq('signal_decision_id', signal_decision_id)
        .execute()
    )
    supabase.table('signal_decisions').update(
        {
            'closing_snapshot_id': closing_snapshot['id'],
            'closing_snapshot_timestamp': closing_snapshot['timestamp'],
            'result_finalized_at': result['finalized_at'],
            'truth_status': 'READY',
        }
    ).eq('id', signal_decision_id).execute()
    return updated.data[0]
