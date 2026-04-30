from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta

from app.db.supabase_admin import assert_supabase_writable
from app.ingestion.data_acquisition import acquire_mlb_day


async def run_once(game_date: date) -> dict[str, int]:
    assert_supabase_writable()
    return await acquire_mlb_day(game_date)


async def run_range(start_date: date, end_date: date) -> dict[str, int]:
    assert_supabase_writable()
    totals = {'games': 0, 'results': 0}
    current = start_date
    while current <= end_date:
        result = await acquire_mlb_day(current)
        totals['games'] += result.get('games', 0)
        totals['results'] += result.get('results', 0)
        current += timedelta(days=1)
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingest MLB games and results.')
    parser.add_argument('--date', default=date.today().isoformat(), help='YYYY-MM-DD date to ingest')
    parser.add_argument('--start-date', help='Optional range start YYYY-MM-DD')
    parser.add_argument('--end-date', help='Optional range end YYYY-MM-DD')
    args = parser.parse_args()

    if args.start_date and args.end_date:
        result = asyncio.run(run_range(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date)))
    else:
        result = asyncio.run(run_once(date.fromisoformat(args.date)))
    print(result, flush=True)


if __name__ == '__main__':
    main()
