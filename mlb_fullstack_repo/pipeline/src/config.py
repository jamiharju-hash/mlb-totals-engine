from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
FEATURE_DIR = DATA_DIR / "features"

SUPABASE_INGEST_URL = os.getenv("SUPABASE_INGEST_URL", "http://localhost:3000/api/ingest/projections")
PIPELINE_INGEST_SECRET = os.getenv("PIPELINE_INGEST_SECRET", "change-me")

for d in [DATA_DIR, RAW_DIR, FEATURE_DIR]:
    d.mkdir(parents=True, exist_ok=True)
