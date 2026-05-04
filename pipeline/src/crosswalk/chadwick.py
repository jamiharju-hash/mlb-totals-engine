from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.src.config import RAW_DIR

CHADWICK_URL = "https://raw.githubusercontent.com/chadwickbureau/register/master/data/people.csv"
CROSSWALK_CACHE = RAW_DIR / "chadwick" / "people.csv"
CACHE_MAX_AGE_DAYS = 7


def _is_stale(path: Path, max_age_days: int = CACHE_MAX_AGE_DAYS) -> bool:
    if not path.exists():
        return True
    age_seconds = pd.Timestamp.utcnow().timestamp() - path.stat().st_mtime
    return age_seconds > max_age_days * 24 * 60 * 60


def get_crosswalk(force_refresh: bool = False) -> pd.DataFrame:
    """Return Chadwick register crosswalk with bbref->MLBAM keys."""
    CROSSWALK_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if force_refresh or _is_stale(CROSSWALK_CACHE):
        df = pd.read_csv(CHADWICK_URL, dtype=str)
        df.to_csv(CROSSWALK_CACHE, index=False)
    else:
        df = pd.read_csv(CROSSWALK_CACHE, dtype=str)

    columns = ["key_bbref", "key_mlbam"]
    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df[columns].copy()
