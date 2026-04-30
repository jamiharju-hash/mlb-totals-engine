from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


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

    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# Backward-compatible alias for modules that expect `client`.
# Prefer get_supabase_admin() in new code so env validation happens at runtime.
client = get_supabase_admin
