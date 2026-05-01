# MLB Totals Engine — Fullstack Projection Platform

Fullstack MLB betting/projection platform using only free/open-source libraries.

## Stack

- Frontend: Next.js App Router
- Backend: Next.js Route Handlers
- Database: Supabase Postgres
- Pipeline: Python, pandas, numpy, requests, scikit-learn, KaggleHub, pybaseball, MLB-StatsAPI
- Deploy: Vercel + Supabase

No paid odds API is required for the MVP. Historical closing odds can come from Kaggle datasets.

## Structure

```text
apps/web/        Next.js dashboard + API routes
pipeline/        Python projection/ingest pipeline
supabase/        SQL migrations + seed
.github/         CI
```

## Local run

### Web

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

### Pipeline

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.run_pipeline
```

## Deploy

Vercel root directory:

```text
apps/web
```

Required Vercel env vars:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
PIPELINE_INGEST_SECRET
```

Apply Supabase migration:

```text
supabase/migrations/001_init_mlb_projection_schema.sql
```
