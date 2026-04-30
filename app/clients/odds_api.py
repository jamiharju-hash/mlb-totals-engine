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
            'markets': markets,
            'oddsFormat': 'american',
            'dateFormat': 'iso',
        }
        # The Odds API accepts either regions or bookmakers. Passing both can
        # reject the request on some plans/endpoints, so prefer explicit
        # bookmakers when configured and otherwise fall back to regions.
        if bookmakers:
            params['bookmakers'] = bookmakers
        else:
            params['regions'] = regions

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f'{self.base_url}/sports/{sport}/odds', params=params)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f'Odds API request failed: {response.status_code} {response.text}') from exc
            return response.json()
