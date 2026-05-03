# MLB Totals Engine — Executive Dashboard Specification

## 1) Overview

### Product name
**MLB Totals Engine**.

### Purpose
An internal operator dashboard that surfaces MLB totals model projections, closing line value (CLV) context, and team market inefficiencies to support daily betting decisions.

### Primary users
- Single operator/analyst (current).
- Potential small internal team of 1–3 users (future).

### Top user outcomes
1. Decide in under 30 seconds whether today’s slate has actionable bets and at what stake.
2. Identify teams systematically mispriced by market (ML / RL / totals).
3. Verify model and data health before committing stake to avoid stale/demo/broken-pipeline decisions.

---

## 2) Scope

### In scope (current phase)
- Projection display.
- CLV tracking context (with explicit fallback limitations).
- Team market value leaderboard.
- Model health monitoring.
- Manual override audit view.
- Data freshness and stale-data warnings.
- CSV export.
- `/api/mlb-dashboard` consolidated route.
- Clean empty-state behavior for legacy diagnostics.

### Out of scope (current phase)
- Live odds feed integration.
- Automated bet placement.
- User accounts / multi-tenancy.
- Mobile-optimized layout.
- Backtesting UI.
- Public-facing access.

---

## 3) Success Criteria / Definition of Done

The phase is complete when:
1. Dashboard loads real projections from Supabase.
2. Fresh vs stale data is correctly identified and surfaced.
3. Bet signals display edge and stake correctly.
4. `/api/mlb-dashboard` exists and returns the consolidated payload contract.
5. Legacy diagnostics section renders clean empty states (no runtime errors) when source tables are empty.
6. The executive rapid-decision workflow can answer all required decision questions from a cold page load in under 30 seconds.

---

## 4) Current Data Architecture (Confirmed)

System has two active layers.

### New executive dashboard tables
- `mlb_projections` (has rows): top picks, edge, stake, confidence, bet signal.
- `mlb_team_market_value` (has rows): team inefficiency leaderboard.
- `mlb_model_metrics` (has rows): model health metrics.
- `mlb_manual_overrides` (currently empty): override audit and operator history.

### Legacy/diagnostic tables
- `predictions_log` (currently empty): future realized ROI, CLV, W-L-P.
- `daily_metrics` (currently empty): future trend metrics.
- `odds_snapshots` (currently empty): future close-line tracking.

---

## 5) KPI Feasibility (Truth-in-Data Rules)

### 5.1 Total ROI %
- **Current status:** Partially computable via proxy.
- **Current source:** `mlb_team_market_value` (team-market ROI proxy, not realized operator ROI).
- **True realized source (once populated):** `predictions_log` using `pnl` and `stake`.
- **UI labeling requirement:** Must label fallback as **“Team market ROI proxy”**.

### 5.2 Current bankroll
- **Formula:** `starting_bankroll + cumulative_pnl`.
- **True source:** `predictions_log` once populated.
- **Config requirement:** Add `STARTING_BANKROLL_UNITS` in app config (default suggested: 100).
- **Empty-table behavior:** Show unavailable/demo message when no settled rows exist.

### 5.3 Record (W-L-P)
- **Current status:** Not derivable from `mlb_projections` today.
- **Reason:** Missing settled outcome fields in `mlb_projections`.
- **Future source:** `predictions_log` (currently totals-oriented and empty) or schema extension on `mlb_projections`.

### 5.4 Today’s top picks
- **Current status:** Fully supported.
- **Source:** `mlb_projections` with sort by edge, confidence, stake.
- **Fallback:** If current date has zero rows, fallback to latest available `game_date` and warn.

### 5.5 Model accuracy / CLV last 30d
- **Current status:** Partially supported.
- **Current source:** `mlb_model_metrics` (`avg_clv_last_250`, simulated ROI/AUC/MAE).
- **True last-30d CLV source (future):** `predictions_log.clv` once populated.

---

## 6) Canonical Source Mapping by Feature

- **Top picks + projection grid:** `mlb_projections`.
- **Team inefficiency leaderboard:** `mlb_team_market_value`.
- **Model health card/panel:** `mlb_model_metrics`.
- **Override audit trail:** `mlb_manual_overrides`.
- **Realized ROI, bankroll, settled W-L-P, true CLV 30d:** `predictions_log` (conditional on data presence).
- **Legacy diagnostic counts:** `predictions_log`, `daily_metrics`, `odds_snapshots` row counts.

---

## 7) API Contract — `/api/mlb-dashboard` (Required)

Endpoint returns:

```ts
type ExecutiveDashboardPayload = {
  summary: {
    activeProjections: number;
    betSignals: number;
    strongBets: number;
    avgEdgePct: number | null;
    maxEdgePct: number | null;
    totalStakeUnits: number | null;
    positiveEdgeRate: number | null;
    bestTeamValue: {
      team: string;
      valueScore: number;
    } | null;
    realizedRoiPct: number | null;
    currentBankrollUnits: number | null;
    record: {
      moneyline: { wins: number; losses: number; pushes: number };
      runline: { wins: number; losses: number; pushes: number };
      total: { wins: number; losses: number; pushes: number };
    } | null;
    clv: {
      avgClvLast30d: number | null;
      clvPositiveRate: number | null;
      settledBets: number;
    };
  };
  topPicks: MlbProjection[];
  projections: MlbProjection[];
  teamMarket: TeamMarketValue[];
  modelMetrics: ModelMetrics | null;
  manualOverrides: ManualOverride[];
  legacyDiagnostics: {
    predictionsLogRows: number;
    dailyMetricsRows: number;
    oddsSnapshotsRows: number;
  };
  dataState: {
    latestProjectionDate: string | null;
    isStale: boolean;
    isDemo: boolean;
    warnings: string[];
  };
};
```

### API behavior requirements
- Must return partial/fallback metrics with explicit labeling where true realized metrics are unavailable.
- Must never error because legacy tables are empty.
- Must return warning list in `dataState.warnings` for stale/demo/empty-result conditions.

---

## 8) Upsert & Write Semantics (Confirmed)

### `mlb_projections`
- Conflict target: `(game_id, team, market, selection)`.
- Supabase upsert `onConflict: "game_id,team,market,selection"`.

### `mlb_team_market_value`
- Current conflict target: `(as_of_date, team)`.
- Future preferred (after adding season): `(season, as_of_date, team)`.

### `mlb_manual_overrides`
- Use **Option A (required)**: deactivate existing active override row, then insert new row.
- Rationale: preserves audit history and avoids partial-index upsert ambiguity.

---

## 9) UI/UX Functional Requirements

1. Show top picks ranked by edge, confidence, then stake.
2. Clearly distinguish actionable vs non-actionable signals.
3. Show explicit stale-data and empty-diagnostic warnings.
4. Separate **proxy metrics** from **realized metrics** in copy and labels.
5. Manual override section must support empty state gracefully.
6. CSV export must include at least: projections, top picks, team market, overrides (even if empty with headers).
7. Cold-load decision flow must prioritize at-a-glance summary first (KPI cards + top picks).

---

## 10) Executive Rapid-Decision Test (Acceptance)

A compliant build must allow an operator to answer, within 30 seconds of cold load:
1. Do we have actionable bets today?
2. How many actionable bets exist?
3. What are the top picks by edge right now?
4. What stake is recommended per actionable pick?
5. Which teams are currently most mispriced?
6. Is projection data fresh enough to trust?
7. Is model health acceptable today?
8. Are manual overrides active and visible/auditable?
9. Are legacy realized-diagnostics unavailable because data is empty (vs because system is broken)?

---

## 11) Data Freshness & State Rules

Because threshold values were not fully finalized, implement configurable defaults:

- `PROJECTIONS_STALE_HOURS` (default TBD in config)
- `TEAM_MARKET_STALE_HOURS` (default TBD in config)
- `MODEL_METRICS_STALE_HOURS` (default TBD in config)

Behavior:
- If latest source timestamp exceeds threshold, set `dataState.isStale = true` and append warning text.
- If synthetic/demo patterns detected, set `dataState.isDemo = true` and append warning text.
- Staleness produces warning state; whether it hard-blocks stake actions should be a config flag (`BLOCK_ACTIONS_ON_STALE`, default false unless policy changes).

---

## 12) Implementation Notes / SQL Intent

- Use `mlb_projections` for live top-picks queries and latest-slate fallback query.
- Use `predictions_log` realized ROI/CLV/W-L-P queries only when settled rows exist.
- Where no realized rows exist, return `null` values for realized metrics and human-readable warnings.

---

## 13) Known Gaps & Planned Schema Evolution

To make ROI/W-L-P/CLV fully real in projection-native workflow, extend `mlb_projections` with settlement + CLV fields:
- Settlement: `result`, `settled_at`, `pnl_units`, `stake_amount_units`.
- Context/meta: `season`, `model_version`, `odds_source`, `bookmaker`, `snapshot_ts`, `updated_at`.
- Odds/CLV: `closing_decimal_odds`, `closing_american_odds`, `closing_implied_probability`, `clv_pct`.

Until this is done (or `predictions_log` is populated), realized performance KPIs remain intentionally partial.

---

## 14) Non-Goals and Guardrails

- Do not present proxy ROI as realized betting ROI.
- Do not synthesize W-L-P from projection-only rows.
- Do not throw API/UI errors when legacy diagnostics tables are empty.
- Do not remove override history for convenience upserts.

---

## 15) Delivery Checklist

- [ ] `/api/mlb-dashboard` route implemented with payload contract.
- [ ] Summary + top picks wired to `mlb_projections`.
- [ ] Team value leaderboard wired to `mlb_team_market_value`.
- [ ] Model health wired to `mlb_model_metrics`.
- [ ] Manual overrides wired with empty-state and audit semantics.
- [ ] Legacy diagnostics row counts wired and empty-safe.
- [ ] Data state warnings (`isStale`, `isDemo`, `warnings[]`) implemented.
- [ ] CSV export implemented for required sections.
- [ ] Proxy-vs-realized KPI labeling verified.
- [ ] 30-second executive test pass verified.
