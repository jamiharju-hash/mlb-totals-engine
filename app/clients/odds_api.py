from __future__ import annotations

import httpx


class OddsAPIClient:
    def __init__(self, base_url: str, api_key: str | None, timeout: float = 20.0):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

    async def totals_odds(
        self,
        *,
        sport: str = 'baseball_mlb',
        regions: str = 'us',
        markets: str = 'totals',
        bookmakers: str | None = None,
    ) -> list[dict]:
        if not self.api_key:
            raise RuntimeError('ODDS_API_KEY is required for odds ingestion')
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': 'american',
            'dateFormat': 'iso',
        }
        if bookmakers:
            params['bookmakers'] = bookmakers
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f'{self.base_url}/sports/{sport}/odds', params=params)
            response.raise_for_status()
            return response.json()
