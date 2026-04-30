from __future__ import annotations

import argparse
import asyncio

from app.ingestion.data_acquisition import acquire_totals_market


async def run_once() -> dict[str, int]:
    return await acquire_totals_market()


async def run_loop(interval_seconds: int) -> None:
    while True:
        result = await run_once()
        print({'worker': 'odds_ingestion', **result}, flush=True)
        await asyncio.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingest MLB totals odds snapshots.')
    parser.add_argument('--loop', action='store_true', help='Run continuously instead of once')
    parser.add_argument('--interval-seconds', type=int, default=300, help='Loop interval. Default: 300 seconds')
    args = parser.parse_args()

    if args.loop:
        asyncio.run(run_loop(args.interval_seconds))
    else:
        print(asyncio.run(run_once()), flush=True)


if __name__ == '__main__':
    main()
