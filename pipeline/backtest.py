from __future__ import annotations

import argparse

import pandas as pd

from app.ev import build_signal


def run_backtest(frame: pd.DataFrame) -> dict:
    required = {'game_id', 'model_total', 'market_total', 'total_runs', 'over_price', 'under_price'}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')

    bankroll = 10_000.0
    starting_bankroll = bankroll
    bets = []
    for row in frame.itertuples(index=False):
        signal = build_signal(
            game_id=str(row.game_id),
            model_total=float(row.model_total),
            market_total=float(row.market_total),
            over_price=int(row.over_price),
            under_price=int(row.under_price),
            edge_threshold_runs=0.25,
            min_ev=0.015,
            bankroll=bankroll,
            kelly_fraction=0.25,
            max_stake_pct=0.02,
        )
        if signal.side.value == 'PASS' or signal.stake <= 0:
            continue
        won = (row.total_runs > row.market_total) if signal.side.value == 'OVER' else (row.total_runs < row.market_total)
        price = int(row.over_price) if signal.side.value == 'OVER' else int(row.under_price)
        profit = signal.stake * (100 / abs(price)) if price < 0 else signal.stake * (price / 100)
        pnl = profit if won else -signal.stake
        bankroll += pnl
        bets.append({'game_id': row.game_id, 'side': signal.side.value, 'stake': signal.stake, 'pnl': pnl})

    total_staked = sum(b['stake'] for b in bets)
    pnl = bankroll - starting_bankroll
    return {
        'bets': len(bets),
        'total_staked': round(total_staked, 2),
        'pnl': round(pnl, 2),
        'roi': round(pnl / total_staked, 4) if total_staked else 0.0,
        'ending_bankroll': round(bankroll, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, help='CSV with model_total, market_total, prices and total_runs')
    args = parser.parse_args()
    print(run_backtest(pd.read_csv(args.data)))


if __name__ == '__main__':
    main()
