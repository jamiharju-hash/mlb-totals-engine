# MLB Totals Dashboard — Vercel Deploy

This frontend is a Next.js dashboard for the MLB Totals Engine.

## Vercel Project Settings

Use the repository root as the Vercel project root. The root-level `vercel.json` handles the monorepo build.

Expected settings:

```text
Framework Preset: Next.js
Install Command: cd frontend && npm install
Build Command: cd frontend && npm run build
Output Directory: frontend/.next
```

## Required Environment Variables

Set these in Vercel Project Settings → Environment Variables:

```env
NEXT_PUBLIC_SUPABASE_URL=https://ohykyscckijbphenugkb.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_jV3R6BovyhHyFIcQ9PNF9Q_HV-fDqBo
```

These are frontend publishable values only. Do not add `SUPABASE_SERVICE_ROLE_KEY` to Vercel frontend environment variables.

## Local Development

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Production Notes

The dashboard reads from Supabase using read-only RLS policies and security-invoker views:

- `dashboard_summary`
- `predictions_log`
- `daily_metrics`
- `metrics_summary`
- `edge_bucket_analysis`

The dashboard will show empty metrics until odds snapshots, logged predictions, closing lines and post-game metrics are populated.
