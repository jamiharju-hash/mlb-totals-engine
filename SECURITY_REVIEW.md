# Security Review (2026-05-03)

Scope: `mlb_fullstack_repo/apps/web`, `frontend`, and selected worker code.

## Findings

1. **Weak webhook authentication for ingest endpoint (high)**
   - `POST /api/ingest/projections` uses a shared static secret in `x-pipeline-secret` and direct string comparison (`provided !== expected`). This is vulnerable to secret replay and lacks defense-in-depth controls such as timestamp/nonce validation and constant-time comparison.
   - Reference: `mlb_fullstack_repo/apps/web/app/api/ingest/projections/route.ts` lines 64-69.
   - Suggested fix:
     - Replace static header check with HMAC signing of the body and timestamp window validation (e.g., `X-Signature`, `X-Timestamp`).
     - Use constant-time comparison (`crypto.timingSafeEqual`) and reject stale timestamps.
     - Add basic per-IP or token-based rate limiting.

2. **Potential unauthenticated data exposure via public API routes (medium)**
   - Public GET routes return full rows (`select("*")`) from `projections`, `team_market_features`, and `model_metrics` with no app-layer auth checks. This relies entirely on database RLS and policy correctness; a future RLS regression would expose data.
   - References:
     - `mlb_fullstack_repo/apps/web/app/api/projections/route.ts` lines 6-13.
     - `mlb_fullstack_repo/apps/web/app/api/team-market/route.ts` lines 6-13.
     - `mlb_fullstack_repo/apps/web/app/api/model-metrics/route.ts` lines 6-13.
   - Suggested fix:
     - Enforce explicit API authentication/authorization (JWT/session) for these endpoints.
     - Replace `select("*")` with allowlisted columns.
     - Add integration tests that verify non-authorized callers cannot read restricted fields.

3. **Error message leakage from backend/database to clients (low-medium)**
   - API handlers return raw `error.message` from Supabase to clients; this can disclose schema/table details and internal query context.
   - References:
     - `mlb_fullstack_repo/apps/web/app/api/ingest/projections/route.ts` lines 84, 92, 97.
     - `mlb_fullstack_repo/apps/web/app/api/projections/route.ts` line 15.
     - `mlb_fullstack_repo/apps/web/app/api/team-market/route.ts` line 15.
     - `mlb_fullstack_repo/apps/web/app/api/model-metrics/route.ts` line 15.
   - Suggested fix:
     - Return generic client-facing errors and log full details server-side only.
     - Standardize error responses with correlation IDs.

4. **Embedded concrete publishable credentials in tracked examples/docs (low)**
   - `.env.example` and README include concrete Supabase project URL and publishable key values. Even if publishable, this increases accidental environment coupling and can aid reconnaissance.
   - References:
     - `frontend/.env.example` lines 1-2.
     - `frontend/README.md` lines 23-25.
   - Suggested fix:
     - Replace with placeholders (`https://<project-ref>.supabase.co`, `sb_publishable_<your-key>`).
     - Add a secret-scanning CI step to prevent accidental commits of sensitive keys.

## Injection/XSS assessment

- No direct SQL string construction or dynamic command execution was identified in reviewed API and worker files.
- Supabase queries use query-builder APIs rather than raw SQL concatenation in reviewed routes.
- No use of `dangerouslySetInnerHTML` detected in reviewed frontend page.

## Authentication/authorization assessment

- Ingest route has authentication, but single-shared-secret model should be hardened.
- Read APIs appear effectively public at app-layer and should not rely solely on RLS for least-privilege guarantees.

## Insecure data handling assessment

- Raw backend error propagation to clients should be reduced.
- Credentials/examples should be normalized to placeholders to avoid confusion and key misuse.
