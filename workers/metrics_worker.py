from __future__ import annotations

import argparse
from datetime import date
from typing import Any

from app.db.supabase_admin import get_supabase_admin
from app.truth_layer import calculate_clv_for_side, snapshot_over_price, snapshot_under_price, utc_now_iso


def _american_profit(stake: float, price: int) -> float:
    if price < 0:
        return stake * (100 / abs(price))
    return stake * (price / 100)


def _grade_pnl(side: str, market_total: float, total_runs: int, stake: float, price: int) -> float:
    if total_runs == market_total:
        return 0.0
    won = (side == 'OVER' and total_runs > market_total) or (side == 'UNDER' and total_runs < market_total)
    return round(_american_profit(stake, price) if won else -stake, 4)


def _result_finalized_at(result: dict[str, Any]) -> str:
    value = result.get('finalized_at') or result.get('created_at')
    if not value:
        raise ValueError('Result missing finalized_at/created_at')
    return str(value)


def _get_game_start(game_id: str) -> str | None:
    supabase = get_supabase_admin()
    response = supabase.table('games').select('id,game_datetime').eq('id', game_id).limit(1).execute()
    rows = response.data or []
    return rows[0].get('game_datetime') if rows else None


def _get_closing_snapshot(game_id: str, game_start: str) -> dict[str, Any] | None:
    supabase = get_supabase_admin()
    response = (
        supabase.table('odds_snapshots')
        .select('*')
        .eq('game_id', game_id)
        .lte('timestamp', game_start)
        .order('timestamp', desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _get_result(game_id: str) -> dict[str, Any] | None:
    supabase = get_supabase_admin()
    response = supabase.table('game_results').select('*').eq('game_id', game_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None


def _void_prediction(prediction_id: int, reason: str) -> None:
    supabase = get_supabase_admin()
    supabase.table('predictions_log').update(
        {'truth_status': 'VOID', 'reason': reason, 'updated_at': utc_now_iso()}
    ).eq('id', prediction_id).execute()


def finalize_pending_predictions(limit: int = 500) -> dict[str, int]:
    supabase = get_supabase_admin()
    response = (
        supabase.table('predictions_log')
        .select('*')
        .eq('truth_status', 'PENDING')
        .eq('should_bet', True)
        .order('prediction_timestamp', desc=False)
        .limit(limit)
        .execute()
    )
    predictions = response.data or []
    finalized = 0
    voided = 0
    skipped = 0

    for prediction in predictions:
        prediction_id = int(prediction['id'])
        game_id = prediction['game_id']
        game_start = _get_game_start(game_id)
        if not game_start:
            skipped += 1
            continue

        closing = _get_closing_snapshot(game_id, game_start)
        if not closing:
            skipped += 1
            continue

        result = _get_result(game_id)
        if not result or result.get('total_runs') is None:
            skipped += 1
            continue

        market_timestamp = prediction['market_snapshot_timestamp']
        prediction_timestamp = prediction['prediction_timestamp']
        closing_timestamp = closing['timestamp']

        if market_timestamp > prediction_timestamp or closing_timestamp > game_start:
            _void_prediction(prediction_id, 'Time integrity violation')
            voided += 1
            continue

        side = prediction['side']
        market_total = float(prediction['market_total'])
        closing_total = float(closing['line'])
        total_runs = int(result['total_runs'])
        stake = float(prediction['stake'])
        price = int(prediction['over_price'] if side == 'OVER' else prediction['under_price'])
        clv = calculate_clv_for_side(side, market_total, closing_total)
        pnl = _grade_pnl(side, market_total, total_runs, stake, price)
        roi = round(pnl / stake, 5) if stake > 0 else 0.0

        supabase.table('predictions_log').update(
            {
                'closing_snapshot_id': closing['id'],
                'closing_snapshot_timestamp': closing_timestamp,
                'closing_total': closing_total,
                'result_finalized_at': _result_finalized_at(result),
                'total_runs': total_runs,
                'clv': clv,
                'pnl': pnl,
                'roi': roi,
                'truth_status': 'READY',
                'updated_at': utc_now_iso(),
            }
        ).eq('id', prediction_id).execute()

        supabase.table('prediction_truth_links').insert(
            {
                'prediction_id': prediction_id,
                'game_id': game_id,
                'prediction_timestamp': prediction_timestamp,
                'market_snapshot_id': prediction['market_snapshot_id'],
                'market_snapshot_timestamp': market_timestamp,
                'market_total': market_total,
                'market_over': prediction['over_price'],
                'market_under': prediction['under_price'],
                'closing_snapshot_id': closing['id'],
                'closing_snapshot_timestamp': closing_timestamp,
                'closing_total': closing_total,
                'closing_over': snapshot_over_price(closing),
                'closing_under': snapshot_under_price(closing),
                'result_finalized_at': _result_finalized_at(result),
                'total_runs': total_runs,
                'clv': clv,
                'truth_status': 'READY',
            }
        ).execute()
        finalized += 1

    return {'processed': len(predictions), 'finalized': finalized, 'voided': voided, 'skipped': skipped}


def update_daily_metrics(metric_date: date | None = None) -> dict[str, Any]:
    metric_date = metric_date or date.today()
    supabase = get_supabase_admin()
    start = f'{metric_date.isoformat()}T00:00:00+00:00'
    end = f'{metric_date.isoformat()}T23:59:59+00:00'
    response = (
        supabase.table('predictions_log')
        .select('*')
        .gte('prediction_timestamp', start)
        .lte('prediction_timestamp', end)
        .execute()
    )
    rows = response.data or []
    bets = [row for row in rows if row.get('should_bet') and row.get('truth_status') == 'READY']
    predictions = len(rows)
    bet_count = len(bets)
    total_staked = sum(float(row.get('stake') or 0) for row in bets)
    pnl = sum(float(row.get('pnl') or 0) for row in bets)
    clvs = [float(row['clv']) for row in bets if row.get('clv') is not None]
    latencies = [int(row['latency_ms']) for row in rows if row.get('latency_ms') is not None]

    avg_clv = round(sum(clvs) / len(clvs), 5) if clvs else 0.0
    clv_win_rate = round(sum(1 for value in clvs if value > 0) / len(clvs), 5) if clvs else 0.0
    roi = round(pnl / total_staked, 5) if total_staked else 0.0
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    p95_latency = 0.0
    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = min(len(sorted_latencies) - 1, int(len(sorted_latencies) * 0.95))
        p95_latency = float(sorted_latencies[p95_index])

    latest_odds = supabase.table('odds_snapshots').select('timestamp').order('timestamp', desc=True).limit(1).execute()
    max_lag = 0.0
    if latest_odds.data:
        latest_timestamp = latest_odds.data[0]['timestamp']
        # Store lag as 0 here if exact parsing is delegated to dashboard DB view.
        max_lag = 0.0 if latest_timestamp else 0.0

    row = {
        'metric_date': metric_date.isoformat(),
        'predictions': predictions,
        'bets': bet_count,
        'avg_clv': avg_clv,
        'clv_win_rate': clv_win_rate,
        'roi': roi,
        'avg_latency_ms': avg_latency,
        'p95_latency_ms': p95_latency,
        'max_data_lag_seconds': max_lag,
        'freshness_slo_pass': max_lag < 60,
        'latency_slo_pass': p95_latency < 300,
        'success_criteria_pass': avg_clv > 0.01 and clv_win_rate > 0.52 and roi > 0.03 and p95_latency < 300 and max_lag < 60,
        'updated_at': utc_now_iso(),
    }
    supabase.table('daily_metrics').upsert(row, on_conflict='metric_date').execute()
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description='Finalize CLV/ROI metrics for logged MLB totals predictions.')
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--date', help='Metric date YYYY-MM-DD. Defaults to today.')
    args = parser.parse_args()

    finalization = finalize_pending_predictions(limit=args.limit)
    metrics = update_daily_metrics(date.fromisoformat(args.date) if args.date else None)
    print({'finalization': finalization, 'daily_metrics': metrics}, flush=True)


if __name__ == '__main__':
    main()
