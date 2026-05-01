# Deploy: Vercel + Supabase

## Supabase

Create a free Supabase project and apply:

```text
supabase/migrations/001_init_mlb_projection_schema.sql
```

## Vercel

Project root:

```text
apps/web
```

Env vars:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
PIPELINE_INGEST_SECRET
NEXT_PUBLIC_SITE_URL
```

## Pipeline

```bash
cd pipeline
cp .env.example .env
pip install -r requirements.txt
python -m src.run_pipeline
```

Set:

```text
SUPABASE_INGEST_URL=https://your-vercel-domain.vercel.app/api/ingest/projections
PIPELINE_INGEST_SECRET=same-as-vercel
```
