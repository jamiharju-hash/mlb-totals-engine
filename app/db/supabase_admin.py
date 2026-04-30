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


def assert_supabase_writable() -> None:
    """Fail fast when the service-role client cannot access required tables."""
    client = get_supabase_admin()
    required_tables = ('games', 'game_results', 'odds_snapshots')
    for table in required_tables:
        try:
            client.table(table).select('*').limit(1).execute()
        except Exception as exc:  # noqa: BLE001 - include table name in operational failure
            raise RuntimeError(f'Supabase preflight failed for table {table}: {exc}') from exc


# Backward-compatible alias for modules that expect `client`.
# Prefer get_supabase_admin() in new code so env validation happens at runtime.
client = get_supabase_admin
