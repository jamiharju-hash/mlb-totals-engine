from __future__ import annotations

from datetime import date

import httpx


class MLBStatsClient:
    def __init__(self, base_url: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    async def schedule(self, game_date: date) -> dict:
        params = {
            'sportId': 1,
            'date': game_date.isoformat(),
            'hydrate': 'team,probablePitcher,linescore',
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f'{self.base_url}/schedule', params=params)
            response.raise_for_status()
            return response.json()

    async def boxscore(self, game_pk: int) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f'{self.base_url}/game/{game_pk}/boxscore')
            response.raise_for_status()
            return response.json()

    async def linescore(self, game_pk: int) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f'{self.base_url}/game/{game_pk}/linescore')
            response.raise_for_status()
            return response.json()
