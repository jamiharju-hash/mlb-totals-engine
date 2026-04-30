from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from supabase import Client, create_client

from app.config import get_settings


def _validate_supabase_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise RuntimeError('SUPABASE_URL must be a full URL, e.g. https://project-ref.supabase.co')


@lru_cache
def get_supabase_admin() -> Client:
    """Return a backend-only Supabase admin client.

    This client uses SUPABASE_SERVICE_ROLE_KEY and must never be exposed to
    browser/client code. The service-role key bypasses RLS by design.
    """
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError('SUPABASE_URL is required')
    if not settings.supabase_service_role_key:
        raise RuntimeError('SUPABASE_SERVICE_ROLE_KEY is required')
    _validate_supabase_url(settings.supabase_url)

    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache
def get_supabase_ingestion_client() -> Client:
    """Return a restricted client for ingestion RPC calls.

    GitHub Actions uses this path so it does not need SUPABASE_SERVICE_ROLE_KEY.
    The database exposes only narrow SECURITY DEFINER RPC functions for this
    client; direct table writes remain blocked by RLS.
    """
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError('SUPABASE_URL is required')
    _validate_supabase_url(settings.supabase_url)

    key = settings.supabase_publishable_key or settings.supabase_anon_key
    if not key:
        raise RuntimeError('SUPABASE_PUBLISHABLE_KEY or SUPABASE_ANON_KEY is required for ingestion RPC')

    return create_client(settings.supabase_url, key)


def assert_supabase_writable() -> None:
    """Fail fast when the ingestion RPC client cannot call required functions."""
    # Use RPC availability instead of direct table writes so GitHub Actions can
    # operate without a service-role secret.
    client = get_supabase_ingestion_client()
    try:
        client.rpc('ingest_mlb_games', {'games_payload': []}).execute()
        client.rpc('ingest_odds_snapshots', {'snapshots_payload': []}).execute()
    except Exception as exc:  # noqa: BLE001 - include operational failure
        raise RuntimeError(f'Supabase ingestion RPC preflight failed: {exc}') from exc


client = get_supabase_admin
