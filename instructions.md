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

### Time Integrity Contract

All data used in predictions must obey the project Time Integrity Contract.

Mandatory rules:

```text
feature_timestamp <= prediction_timestamp
market_snapshot_timestamp <= prediction_timestamp
closing_snapshot_timestamp <= game_start_timestamp
no post-game data in features
```

The market line used for prediction must be the line available at prediction time. The closing line must be the last available valid line before game start. Any violation invalidates CLV, backtest results, and model evaluation for the affected prediction.

Full contract: `docs/time_integrity_contract.md`.

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
├── docs/
│   └── time_integrity_contract.md
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

### Documentation

#### `docs/time_integrity_contract.md`

Mandatory validity contract for predictions, CLV, backtests, ROI, and model evaluation. Any violation invalidates the affected record.

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

### Time Integrity Contract

This is mandatory. It is not a best-practice note.

Every prediction, backtest row, CLV calculation, and model evaluation must satisfy:

```text
feature_timestamp <= prediction_timestamp
market_snapshot_timestamp <= prediction_timestamp
closing_snapshot_timestamp <= game_start_timestamp
```

No post-game data is allowed in features.

The prediction-time market line must be selected as:

```text
latest odds snapshot where timestamp <= prediction_timestamp
```

The closing line must be selected as:

```text
latest odds snapshot where timestamp <= game_start_timestamp
```

If this cannot be proven, mark the record `VOID` or keep it `PENDING`. Do not include it in CLV, ROI, backtest, calibration, model evaluation, or success criteria metrics.

Full contract: `docs/time_integrity_contract.md`.

### Python Style

- Use Python 3.12-compatible syntax.
- Use type hints for public functions.
- Use `from __future__ import annotations` in new Python modules.
- Use `dataclass(frozen=True)` for immutable value objects when appropriate.
- Use Pydantic models for API request/response schemas.
- Keep pure calculation functions side-effect free.
- Isolate database writes behind explicit functions.
- Avoid import-time failures from missing secrets. Use lazy initialization for clients that require env variables.

### Time-Consistency Rules

All evaluation records must satisfy:

```text
market_snapshot_timestamp <= prediction_timestamp
feature_timestamp <= prediction_timestamp
closing_snapshot_timestamp <= game_start_timestamp
result_finalized_at >= game_start_timestamp
```

No feature or market input may come from the future relative to the prediction timestamp. No closing line may come from after game start.

### ML Standards

- Use `TimeSeriesSplit` for model validation.
- Do not randomly shuffle historical sports data for validation.
- Separate raw model prediction from calibrated prediction.
- Store model artifacts under `models/`, but do not commit binary model files.
- Evaluate by CLV and post-vig ROI, not only MAE/RMSE.
- Backtests must use only features available before prediction time.
- Backtests must exclude or mark `VOID` any row that violates the Time Integrity Contract.

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
- Logged records obey the Time Integrity Contract.

#### Evaluation Flow

As an operator, I want predictions, closing lines, and results joined into a single evaluation layer so that I can validate whether the model beats closing markets.

Acceptance criteria:

- Closing line is reconstructed from the last valid odds snapshot before game start.
- CLV is calculated by side.
- Bets are graded after final result.
- ROI is calculated post-vig.
- Daily metrics update `daily_metrics`.
- Records violating time integrity are excluded from metrics.

---

## 6. APIs and Integrations

### FastAPI Service

#### `GET /health`

Returns service status and model/calibrator load state.

#### `POST /predict`

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

### Closing Line Reconstruction

Closing line reconstruction must select the latest valid market snapshot before game start.

Required invariant:

```text
prediction_timestamp <= closing_snapshot_timestamp <= game_start_timestamp
```

If game start timestamp is unavailable, do not treat the latest arbitrary snapshot as production-grade closing line. Mark evaluation as `PENDING` or `VOID` until the cutoff is reliable.

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

CLV must not be calculated if the Time Integrity Contract is violated.

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

## 8. Prompt Guardrails for Route Refactors

### Prompt 1

- Refactor the existing `frontend/app/api/mlb-dashboard/route.ts`.
- Do not create a second route file.
- Preserve exported `GET` handler signature and Next.js route conventions.

### Final Acceptance Check

- Search for duplicate `mlb-dashboard` route handlers; there must be exactly one.
