from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
FEATURE_DIR = DATA_DIR / "features"
EXPORT_DIR = DATA_DIR / "exports"

SUPABASE_INGEST_URL = os.getenv("SUPABASE_INGEST_URL", "http://localhost:3000/api/ingest/projections")
PIPELINE_INGEST_SECRET = os.getenv("PIPELINE_INGEST_SECRET", "")

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")


def validate_runtime_env() -> None:
    if PIPELINE_INGEST_SECRET in ("", "change-me", "<random-secret-min-32-chars>"):
        raise RuntimeError(
            "PIPELINE_INGEST_SECRET is not set. Copy .env.example to .env and set a random secret "
            "that matches the Vercel PIPELINE_INGEST_SECRET environment variable."
        )

    if SUPABASE_INGEST_URL in ("", "https://your-vercel-domain.vercel.app/api/ingest/projections"):
        raise RuntimeError("SUPABASE_INGEST_URL is not configured.")


for d in [DATA_DIR, RAW_DIR, INTERIM_DIR, FEATURE_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)
