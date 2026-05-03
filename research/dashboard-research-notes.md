# Dashboard Research Notes

Date: 2026-05-03

## Objective

Research the current MLB totals/projection dashboard implementation and determine the safest path to build a fully featured analytics dashboard on Vercel + Supabase using free/open-source libraries.

## Current working hypotheses

### H1 — Production deploy builds from `frontend/`, not `apps/web/`

- Confidence: 0.95
- Severity if ignored: Critical
- Evidence:
  - Root `package.json` has workspace list containing only `frontend`.
  - Root build script is `npm --workspace frontend run build`.
  - Vercel build log also ran `npm --workspace frontend run build`.
- Implication:
  - Any dashboard implementation under `mlb_fullstack_repo/apps/web` or `apps/web` will not be served unless Vercel/root workspace settings are changed.
- Current plan:
  - Implement dashboard upgrades in `frontend/` unless repo is intentionally restructured.

### H2 — Existing deployed dashboard is totals-specific and already reads Supabase directly from the browser

- Confidence: 0.85
- Severity if ignored: High
- Evidence:
  - `frontend/app/page.tsx` is a client component.
  - It calls `getSupabaseClient()` and queries `dashboard_summary`, `predictions_log`, and `daily_metrics`.
  - It displays CLV, ROI, data lag, active signals, and totals-focused signals.
- Implication:
  - The current app is not empty. The correct implementation is likely an expansion/refactor, not a greenfield replacement.

### H3 — Supabase environment variable naming is inconsistent

- Confidence: 0.90
- Severity if ignored: High
- Evidence:
  - Current `frontend/lib/supabase.ts` expects `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
  - Later scaffold/docs used `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Implication:
  - Vercel can build successfully but runtime can fail with missing env var errors.
- Current plan:
  - Support both names or standardize docs and code.

### H4 — Supabase schema for current frontend tables may be missing from repo

- Confidence: 0.80
- Severity if ignored: High
- Evidence:
  - `frontend/app/page.tsx` references `dashboard_summary`, `predictions_log`, and `daily_metrics`.
  - Repository search did not find SQL definitions for those names.
- Implication:
  - New deploys are hard to reproduce; a fresh Supabase project may not work.
- Current plan:
  - Add migrations for existing table/view dependencies or migrate frontend to new schema.

### H5 — The requested analytics dashboard should be built into the active `frontend/` workspace

- Confidence: 0.90
- Severity if ignored: Critical
- Evidence:
  - H1 confirms active build path.
  - H2 confirms existing UI surface and dependencies are already in `frontend`.
- Implication:
  - Use `frontend/app`, `frontend/components`, and `frontend/lib`, not nested scaffolds.

## Competing implementation paths

### Path A — Expand current `frontend` dashboard in place

- Confidence: 0.90
- Pros:
  - Matches production Vercel build path.
  - Uses existing Supabase client and Recharts dependency.
  - Least deploy risk.
- Cons:
  - Must adapt existing totals-specific schema or add compatibility layer.

### Path B — Switch Vercel root to `apps/web`

- Confidence: 0.45
- Pros:
  - Cleaner long-term monorepo structure.
- Cons:
  - Higher deployment risk.
  - Existing production app uses `frontend` workspace.
  - Requires Vercel settings and package workspace changes.

### Path C — Keep both dashboards temporarily

- Confidence: 0.55
- Pros:
  - Safer migration path.
- Cons:
  - Increases confusion and duplicate code.
  - Could perpetuate wrong-build-path issues.

## Research findings so far

1. Production build path is confirmed as `frontend`.
2. Current frontend already includes Supabase and Recharts.
3. Current UI is totals/CLV-oriented, not full market projection/ROI-oriented.
4. Current Supabase key name differs from newer scaffold docs.
5. Schema definitions for current frontend tables were not found in repo search.

## Self-critique

- I should not assume missing schema solely from one file lookup; I performed repository searches for the referenced table names, but this should be verified again after inspecting full tree or Supabase project state.
- I should not overwrite the existing UI blindly; it contains useful CLV/ROI concepts that should be preserved.
- The safest implementation is a refactor/expansion of `frontend`, not a new nested app.

## Next steps

1. Add/confirm Supabase migration for the tables/views the current frontend expects.
2. Add compatibility for both `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
3. Implement enhanced analytics dashboard in `frontend/app/page.tsx` and supporting components.
4. Add filters/search/sort/stale-data diagnostics.
5. Add API/data diagnostics or clear UI error states.
6. Add tests for pipeline math and closing odds utilities.
