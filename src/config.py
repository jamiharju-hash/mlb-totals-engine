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

DASHBOARD_OUTPUT = Path(
    os.getenv(
        "DASHBOARD_OUTPUT",
        str(PROJECT_DIR.parent / "web" / "public" / "data" / "dashboard.json"),
    )
)

for d in [DATA_DIR, RAW_DIR, INTERIM_DIR, FEATURE_DIR, EXPORT_DIR, DASHBOARD_OUTPUT.parent]:
    d.mkdir(parents=True, exist_ok=True)
