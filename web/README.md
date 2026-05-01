# MLB Projection Dashboard

## Run locally

```bash
npm install
npm run dev
```

## Data

The UI loads:

```text
public/data/dashboard.json
```

Generate it from the Python pipeline:

```bash
cd ../pipeline
python -m src.run_pipeline
```

## Deploy

Deploy this `web/` folder to Vercel.
