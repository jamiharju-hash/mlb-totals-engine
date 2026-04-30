from __future__ import annotations

import pandas as pd


def calculate_clv(row: pd.Series) -> float:
    """Closing Line Value in runs.

    OVER bet is good when closing total is higher than bet line.
    UNDER bet is good when closing total is lower than bet line.
    """
    side = str(row['side']).upper()
    bet_line = float(row['market_total'])
    closing_line = float(row['closing_total'])
    if side == 'OVER':
        return closing_line - bet_line
    if side == 'UNDER':
        return bet_line - closing_line
    return 0.0


def grade_bet(row: pd.Series) -> float:
    side = str(row['side']).upper()
    total_runs = float(row['total_runs'])
    line = float(row['market_total'])
    stake = float(row.get('stake', 1.0))
    price = int(row['over_price']) if side == 'OVER' else int(row['under_price'])

    if total_runs == line:
        return 0.0

    won = (side == 'OVER' and total_runs > line) or (side == 'UNDER' and total_runs < line)
    if not won:
        return -stake
    if price < 0:
        return stake * (100 / abs(price))
    return stake * (price / 100)


def evaluate_betting_performance(frame: pd.DataFrame) -> dict:
    required = {'side', 'market_total', 'closing_total', 'total_runs', 'over_price', 'under_price'}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required performance columns: {sorted(missing)}')

    bets = frame[frame['side'].isin(['OVER', 'UNDER'])].copy()
    if bets.empty:
        return {'bets': 0, 'roi': 0.0, 'pnl': 0.0, 'avg_clv': 0.0, 'clv_win_rate': 0.0}

    if 'stake' not in bets.columns:
        bets['stake'] = 1.0

    bets['clv'] = bets.apply(calculate_clv, axis=1)
    bets['pnl'] = bets.apply(grade_bet, axis=1)
    total_staked = float(bets['stake'].sum())
    pnl = float(bets['pnl'].sum())
    return {
        'bets': int(len(bets)),
        'total_staked': round(total_staked, 4),
        'pnl': round(pnl, 4),
        'roi': round(pnl / total_staked, 5) if total_staked else 0.0,
        'avg_clv': round(float(bets['clv'].mean()), 5),
        'clv_win_rate': round(float((bets['clv'] > 0).mean()), 5),
    }
