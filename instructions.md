# MLB Totals Engine — Project Instructions

## 1. Overview

### Project Goal

MLB Totals Engine is a production-grade betting intelligence platform for MLB game totals. The system predicts total runs for MLB games, compares those predictions against market totals, identifies potential positive expected value (+EV) opportunities, and validates edge using Closing Line Value (CLV) rather than raw prediction accuracy alone.

The product is designed for an internal operator / quant workflow first. External paid subscriber functionality is explicitly out of scope for the MVP.

### Problem Statement

Sports betting prediction systems often optimize for accuracy without proving that they beat the market. For betting use cases, raw prediction error is insufficient. A useful system must show that its prices beat closing lines and generate post-vig return under realistic constraints.

This project solves that by building a closed-loop intelligence system where:

1. MLB Stats API provides game reality and ground truth.
2. The Odds API provides market totals and price signals.
3. Feature engineering converts game, pitcher, lineup, bullpen, park, weather, and market data into model inputs.
4. XGBoost predicts continuous total runs.
5. Market distribution calibration constrains model output to realistic market-relative ranges.
6. EV and Kelly logic convert model edge into bet/no-bet decisions.
7. Predictions are logged with time-consistent market snapshots.
8. Closing lines and final results are linked back to predictions for CLV, ROI, latency, and data freshness measurement.
9. A dashboard exposes system health, active signals, CLV, ROI, bet count, and data lag.

### Non-Negotiable Success Criteria

The system should be evaluated against these production criteria:

| Metric | Target |
|---|---:|
| Average CLV | > +1.0% |
| CLV Win Rate | > 52% |
| ROI post-vig, simulated | > 3% |
| Decision Latency | < 300ms |
| Data Freshness | < 60s lag |

A model should not be considered production-valid unless it demonstrates positive CLV over a meaningful sample. ROI without positive CLV should be treated as variance, not durable edge.

### Core Functionality

The MVP includes:

- MLB totals prediction API.
- Odds snapshot ingestion.
- MLB game and result ingestion.
- Feature engineering pipeline.
- XGBoost regression training.
- Market distribution calibration.
- EV calculation vs market line.
- Kelly staking fraction calculation.
- Bet/no-bet decision engine.
- Canonical `predictions_log` table.
- Time-consistent truth layer linking prediction timestamp, market snapshot, closing snapshot, and result finalization.
- CLV and ROI metric surfaces.
- Internal read-only dashboard using Supabase publishable client.

Explicitly not included in MVP:

- Auto betting.
- Multi-user authentication.
- Multi-sport expansion.
- Arbitrage engine.
- Stripe subscriber system.
- Push notifications.
- Steam detection.

---

## 2. Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---:|---|
| Python | 3.12 recommended | Backend runtime |
| FastAPI | 0.115.6 | API layer |
| Uvicorn | 0.34.0 | ASGI server |
| Pydantic | 2.10.4 | Request/response schemas |
| Pydantic Settings | 2.7.0 | Environment-based config |
| HTTPX | 0.28.1 | Async HTTP clients for MLB Stats API and Odds API |
| Pandas | 2.2.3 | Data manipulation and feature pipelines |
| NumPy | 2.2.1 | Numeric computation and calibration |
| Scikit-learn | 1.6.0 | TimeSeriesSplit and metrics |
| XGBoost | 2.1.3 | Total-runs regression model |
| Joblib | 1.4.2 | Model and calibrator artifact persistence |
| python-dotenv | 1.0.1 | Local env loading |
| Supabase Python | 2.10.0 | Backend Supabase admin client |
| Pytest | 8.3.4 | Tests |
| Ruff | 0.8.4 | Python linting |

### Database and Storage

| Technology | Purpose |
|---|---|
| Supabase Postgres | Primary persistence layer |
| Supabase RLS | Row-level security enforcement |
| Supabase service role key | Backend-only admin access |
| Supabase publishable key | Frontend read-only dashboard access |

### Frontend

| Technology | Version | Purpose |
|---|---:|---|
| Next.js | ^15.1.3 | React frontend framework |
| React | ^19.0.0 | UI layer |
| React DOM | ^19.0.0 | DOM renderer |
| TypeScript | ^5.7.2 | Static typing |
| Tailwind CSS | ^3.4.17 | Styling |
| Recharts | ^2.15.0 | CLV and ROI charts |
| @supabase/supabase-js | ^2.48.1 | Browser read-only Supabase client |
| ESLint | ^9.17.0 | Frontend linting |
| eslint-config-next | ^15.1.3 | Next.js lint config |

### External APIs

| Service | Purpose |
|---|---|
| MLB Stats API | Games, schedules, pitchers, lineups, teams, results |
| The Odds API | Totals market odds snapshots |

### Optional Future Infrastructure

| Technology | Purpose |
|---|---|
| Redis | Optional cache / worker queue layer |
| Stripe | V1 subscriber system |
| Push provider | V1 signal notifications |

---

## 3. Project Structure

```text
mlb-totals-engine/
├── app/
│   ├── clients/
│   │   ├── mlb_stats.py
│   │   └── odds_api.py
│   ├── db/
│   │   └── supabase_admin.py
│   ├── ingestion/
│   │   ├── data_acquisition.py
│   │   └── odds_store.py
│   ├── __init__.py
│   ├── calibration.py
│   ├── config.py
│   ├── ev.py
│   ├── main.py
│   ├── model.py
│   ├── schemas.py
│   ├── signals.py
│   └── truth_layer.py
├── pipeline/
│   ├── __init__.py
│   ├── backtest.py
│   ├── feature_engineering.py
│   ├── metrics.py
│   └── train.py
├── supabase/
│   └── migrations/
│       ├── 001_force_rls_all_tables.sql
│       ├── 002_signal_decisions.sql
│       ├── 003_core_betting_tables.sql
│       ├── 004_time_consistent_truth_layer.sql
│       ├── 005_predictions_features_metrics.sql
│       └── 006_dashboard_read_models.sql
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── lib/
│   │   └── supabase.ts
│   ├── .env.example
│   ├── next.config.ts
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── tests/
│   └── test_ev.py
├── .env.backend.example
├── .env.example
├── .gitignore
├── README.md
├── instructions.md
└── requirements.txt
```

### Backend Directories

#### `app/`

Application code for the FastAPI service and betting engine.

- `main.py`: FastAPI app and `/predict` endpoint.
- `config.py`: Environment settings via Pydantic Settings.
- `schemas.py`: API models including `PredictionRequest`, `GameFeatures`, `BetSignal`, and calibration details.
- `model.py`: Total-runs model wrapper. Loads XGBoost artifact when available and provides deterministic fallback behavior.
- `calibration.py`: Market distribution calibration layer.
- `ev.py`: Edge calculation, expected value, Kelly fraction, staking, and bet/no-bet logic.
- `signals.py`: Structured signal payloads, prediction logging, and latency timer.
- `truth_layer.py`: Time-consistent truth linkage between prediction timestamp, market snapshot, closing snapshot, and final result.

#### `app/clients/`

External API clients.

- `mlb_stats.py`: Async MLB Stats API client.
- `odds_api.py`: Async The Odds API totals client.

#### `app/db/`

Database clients.

- `supabase_admin.py`: Backend-only Supabase admin client using `SUPABASE_SERVICE_ROLE_KEY`. Never expose this in frontend code.

#### `app/ingestion/`

Data acquisition and persistence helpers.

- `data_acquisition.py`: Normalizes MLB schedule/results and totals odds snapshots.
- `odds_store.py`: Stores odds snapshots with validation and timestamp normalization.

### Pipeline Directory

#### `pipeline/`

Offline and worker-style scripts.

- `feature_engineering.py`: Builds model-ready features including pitching differential, offensive efficiency, bullpen fatigue, lineup strength, park/weather adjustments, and market embeddings.
- `train.py`: Trains XGBoost model using `TimeSeriesSplit` and saves both model and market calibrator artifacts.
- `backtest.py`: Simulates historical betting decisions.
- `metrics.py`: Calculates CLV, grades bets, and evaluates ROI.

### Supabase Migrations

#### `supabase/migrations/`

Database schema and RLS migrations.

- `001_force_rls_all_tables.sql`: Enables and forces RLS across public tables.
- `002_signal_decisions.sql`: Legacy signal decision audit table.
- `003_core_betting_tables.sql`: Core tables: `games`, `odds_snapshots`, `game_results`, `model_runs`.
- `004_time_consistent_truth_layer.sql`: Adds timestamp linkage and `prediction_truth_links`.
- `005_predictions_features_metrics.sql`: Adds canonical `predictions_log`, `features`, `bets`, and `daily_metrics`.
- `006_dashboard_read_models.sql`: Adds dashboard read policies, `market_phase`, indexes, and `dashboard_summary` view.

### Frontend Directory

#### `frontend/`

Internal operator dashboard.

- `app/page.tsx`: Main dashboard screen with health cards, CLV chart, ROI chart, and active/recent signals table.
- `app/layout.tsx`: Root layout and metadata.
- `app/globals.css`: Tailwind base styles.
- `lib/supabase.ts`: Browser Supabase client using publishable key only.
- `.env.example`: Frontend env variables.
- `package.json`: Next.js frontend dependencies and scripts.

### Tests

#### `tests/`

- `test_ev.py`: Unit tests for odds conversion, EV thresholding, and bet signal generation.

---

## 4. Coding Standards

### General Principles

1. Prefer explicit, typed interfaces.
2. Avoid hidden time leakage. Every prediction, feature, market snapshot, closing snapshot, and result must be timestamped.
3. Treat CLV as the primary validation metric.
4. Treat ROI as secondary until CLV is positive over a meaningful sample.
5. Never expose service role keys to browser code.
6. Keep prediction logic deterministic and audit-friendly.
7. Log both bet and no-bet decisions where relevant.
8. Use market timestamps available at prediction time only.

### Python Style

- Use Python 3.12-compatible syntax.
- Use type hints for public functions.
- Use `from __future__ import annotations` in new Python modules.
- Use `dataclass(frozen=True)` for immutable value objects when appropriate.
- Use Pydantic models for API request/response schemas.
- Keep pure calculation functions side-effect free.
- Isolate database writes behind explicit functions.
- Avoid import-time failures from missing secrets. Use lazy initialization for clients that require env variables.

### Python Linting

Ruff is the configured Python linter.

Run:

```bash
ruff check app pipeline tests
```

### Python Testing

Run:

```bash
pytest -q
```

Recommended test categories:

- EV and Kelly math.
- Bet/no-bet decision thresholds.
- CLV calculation for OVER and UNDER.
- Timestamp-order constraints.
- Calibration behavior.
- Prediction logging payload integrity.

### FastAPI Standards

- Endpoint responses must use Pydantic response models.
- `/predict` must return a structured `BetSignal`.
- Logging should be opt-in via `log_decision` to avoid polluting production tables during dry runs.
- Request latency should be measured server-side.
- Prediction logging must use the latest market snapshot with `timestamp <= prediction_timestamp`.

### Supabase / Database Standards

- RLS must be enabled and forced on all public tables.
- Service role key must be backend-only.
- Frontend uses publishable key and SELECT-only policies.
- Canonical evaluation should use `predictions_log`, not legacy `signal_decisions`.
- `predictions_log` must preserve:
  - `prediction_timestamp`
  - `market_snapshot_timestamp`
  - `closing_snapshot_timestamp`
  - `result_finalized_at`
  - `latency_ms`
  - `truth_status`
- Never update historical prediction inputs after logging. Add derived evaluation fields only after closing/result availability.

### Time-Consistency Rules

All evaluation records must satisfy:

```text
market_snapshot_timestamp <= prediction_timestamp
feature_timestamp <= prediction_timestamp
closing_snapshot_timestamp >= prediction_timestamp
result_finalized_at >= prediction_timestamp
```

No feature or market input may come from the future relative to the prediction timestamp.

### ML Standards

- Use `TimeSeriesSplit` for model validation.
- Do not randomly shuffle historical sports data for validation.
- Separate raw model prediction from calibrated prediction.
- Store model artifacts under `models/`, but do not commit binary model files.
- Evaluate by CLV and post-vig ROI, not only MAE/RMSE.
- Backtests must use only features available before prediction time.

### Frontend Standards

- Use TypeScript with strict mode.
- Use Tailwind utility classes.
- Keep Supabase frontend client read-only.
- Use dashboard views and read-only tables only.
- Do not include service role keys or backend secrets in frontend env files.
- Use `NEXT_PUBLIC_` prefix only for safe publishable frontend values.

### Environment Files

Backend local runtime:

```bash
cp .env.backend.example .env
```

Frontend local runtime:

```bash
cd frontend
cp .env.example .env.local
```

Never commit real `.env` files.

---

## 5. User Stories

### Internal Operator / Quant

#### Prediction Flow

As an operator, I want to submit a game and market line to `/predict` so that I receive a structured OVER/UNDER/PASS decision with model total, market total, edge, EV, probability, stake, confidence, and reason.

Acceptance criteria:

- Endpoint returns in under 300ms under normal operating conditions.
- Response includes raw and calibrated model total.
- Response includes EV and Kelly-based stake.
- Response includes bet/no-bet decision.
- Optional logging writes to `predictions_log`.

#### Decision Logging Flow

As an operator, I want every logged prediction to include the market snapshot available at prediction time so that CLV and ROI can be audited without leakage.

Acceptance criteria:

- `market_snapshot_timestamp <= prediction_timestamp`.
- Prediction record stores request and response timestamps.
- Prediction record stores latency in milliseconds.
- Prediction record starts with `truth_status = PENDING`.

#### Daily Pipeline Flow

As an operator, I want scheduled workers to ingest games, odds, features, predictions, and results so that the system continuously updates the betting intelligence loop.

Acceptance criteria:

- Odds ingestion runs every 5 minutes.
- MLB data ingestion runs hourly.
- Training runs weekly.
- Metrics worker runs post-game.
- Data lag remains below 60 seconds for live odds snapshots when the system is active.

#### Evaluation Flow

As an operator, I want predictions, closing lines, and results joined into a single evaluation layer so that I can validate whether the model beats closing markets.

Acceptance criteria:

- Closing line is reconstructed from odds snapshots.
- CLV is calculated by side.
- Bets are graded after final result.
- ROI is calculated post-vig.
- Daily metrics update `daily_metrics`.

#### Dashboard Flow

As an operator, I want a dashboard that shows current health and edge visibility so that I can quickly determine whether the system is performing.

Acceptance criteria:

- Dashboard shows today’s games.
- Dashboard shows active signals.
- Dashboard shows 7-day average CLV.
- Dashboard shows rolling ROI.
- Dashboard shows bet count.
- Dashboard shows data lag.
- Dashboard includes CLV and ROI charts.
- Dashboard uses read-only Supabase client.

### External Paid Subscriber — V1 Optional

As a subscriber, I want to consume signals only, without access to internal model logs, feature data, or operational dashboards.

This is out of scope for MVP and belongs to a future V1 extension with Stripe, auth, signal feed API, and push notifications.

---

## 6. APIs and Integrations

### FastAPI Service

#### `GET /health`

Purpose:

Returns service status and model/calibrator load state.

Example response:

```json
{
  "status": "ok",
  "model_loaded": true,
  "calibrator_loaded": true
}
```

#### `POST /predict`

Purpose:

Predicts MLB total runs, calibrates output to market distribution, calculates EV and Kelly stake, determines bet/no-bet decision, and optionally logs the decision.

Responsibilities:

1. Feature validation.
2. Model inference.
3. Market distribution calibration.
4. EV calculation.
5. Kelly staking.
6. Bet/no-bet decision.
7. Optional canonical logging to `predictions_log`.
8. Latency measurement.
9. Time-consistent market snapshot linkage.

Example request:

```json
{
  "features": {
    "game_id": "nyy-bos-2026-04-30",
    "home_team": "BOS",
    "away_team": "NYY",
    "market_total": 8.5,
    "over_price": -105,
    "under_price": -115,
    "home_sp_era": 4.6,
    "away_sp_era": 4.2,
    "home_bullpen_era_7d": 4.8,
    "away_bullpen_era_7d": 3.9,
    "home_ops_14d": 0.760,
    "away_ops_14d": 0.780,
    "park_factor": 1.05,
    "temperature_f": 74,
    "wind_out_mph": 8
  },
  "log_decision": true
}
```

Example response:

```json
{
  "game_id": "nyy-bos-2026-04-30",
  "side": "OVER",
  "model_total": 8.72,
  "raw_model_total": 8.95,
  "market_total": 8.5,
  "edge_runs": 0.22,
  "estimated_probability": 0.538,
  "break_even_probability": 0.5122,
  "expected_value": 0.027,
  "stake": 50.0,
  "confidence": "MEDIUM",
  "reason": "Model total exceeds market threshold with positive expected value.",
  "calibration": {
    "raw_total": 8.95,
    "calibrated_total": 8.72,
    "residual_vs_market": 0.22,
    "market_percentile": 0.55,
    "model_percentile": 0.61,
    "calibration_method": "empirical_quantile_market_distribution"
  },
  "decision_logged": true
}
```

### MLB Stats API Integration

Client:

```text
app/clients/mlb_stats.py
```

Used for:

- Daily schedule.
- Game metadata.
- Teams.
- Probable pitchers.
- Boxscores.
- Linescores.
- Final scores and total runs.

Primary acquisition function:

```python
await acquire_mlb_day(game_date)
```

Storage targets:

- `games`
- `game_results`

### The Odds API Integration

Client:

```text
app/clients/odds_api.py
```

Used for:

- MLB totals market snapshots.
- Bookmaker totals lines.
- Over/under prices.
- Market timestamps.

Primary acquisition function:

```python
await acquire_totals_market()
```

Storage target:

- `odds_snapshots`

Required production behavior:

- Run every 5 minutes or faster if API quota allows.
- Store every snapshot.
- Tag market phase:
  - `opening`
  - `pre_lineup`
  - `post_lineup`
  - `closing`
  - `unknown`
- Preserve original timestamp.
- Do not overwrite historical snapshots.

### Supabase Backend Integration

Backend admin client:

```text
app/db/supabase_admin.py
```

Usage:

```python
from app.db.supabase_admin import get_supabase_admin

supabase = get_supabase_admin()
```

Required env:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Rules:

- Use only in backend code.
- Never import or expose this in frontend.
- Service role bypasses RLS and must be treated as a secret.

### Supabase Frontend Integration

Frontend client:

```text
frontend/lib/supabase.ts
```

Required env:

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

Rules:

- Read-only dashboard usage only.
- Must not use service role key.
- Relies on SELECT-only RLS policies.

### Database Tables

Core tables:

| Table | Purpose |
|---|---|
| `games` | MLB schedule and game metadata |
| `odds_snapshots` | Market totals snapshots over time |
| `features` | Internal feature snapshots |
| `predictions_log` | Canonical prediction and evaluation log |
| `game_results` | Final score and total runs ground truth |
| `prediction_truth_links` | Time-consistent linkage between prediction, market, closing, and result |
| `signal_decisions` | Legacy structured signal audit log |
| `model_runs` | Training run metadata and model metrics |
| `bets` | Optional paper/execution layer |
| `daily_metrics` | Dashboard metrics and success criteria tracking |

### Closing Line Reconstruction

Closing line reconstruction should select the latest valid market snapshot before first pitch or another approved cutoff.

Required invariant:

```text
prediction_timestamp <= closing_snapshot_timestamp <= game_start_timestamp
```

If game start timestamp is unavailable, do not treat the latest arbitrary snapshot as production-grade closing line. Mark evaluation as pending or unknown until the cutoff is reliable.

### CLV Calculation

For OVER:

```text
CLV = closing_total - bet_market_total
```

For UNDER:

```text
CLV = bet_market_total - closing_total
```

Positive CLV means the bet beat the closing market.

### Metrics Service

The metrics worker should run post-game and update:

- `predictions_log.closing_snapshot_id`
- `predictions_log.closing_snapshot_timestamp`
- `predictions_log.closing_total`
- `predictions_log.total_runs`
- `predictions_log.clv`
- `predictions_log.pnl`
- `predictions_log.roi`
- `predictions_log.truth_status`
- `daily_metrics.avg_clv`
- `daily_metrics.clv_win_rate`
- `daily_metrics.roi`
- `daily_metrics.avg_latency_ms`
- `daily_metrics.p95_latency_ms`
- `daily_metrics.max_data_lag_seconds`
- `daily_metrics.success_criteria_pass`

### Dashboard Integration

Frontend reads from:

- `dashboard_summary`
- `predictions_log`
- `daily_metrics`

Main dashboard components:

- Today’s games.
- Active signals.
- Avg CLV last 7 days.
- Rolling ROI.
- Bet count.
- Data lag.
- CLV chart.
- ROI chart.
- Recent active signals table.

### Local Development Commands

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.backend.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Tests and lint:

```bash
ruff check app pipeline tests
pytest -q
```

Training:

```bash
python pipeline/train.py \
  --data data/processed/training.csv \
  --out models/xgb_totals.joblib \
  --calibrator-out models/market_calibrator.joblib
```

Backtest:

```bash
python pipeline/backtest.py --data data/processed/backtest_predictions.csv
```
