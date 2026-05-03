#!/usr/bin/env python3
"""Ingest Kaggle MLB odds datasets into Supabase raw staging tables.

This script intentionally writes to raw_kaggle_datasets and raw_kaggle_odds only.
Do not normalize into odds_snapshots until the source-specific column semantics have
been validated.

Required env vars:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY

Optional env vars:
  KAGGLE_DATASETS=slug1,slug2
  KAGGLE_MAX_ROWS=1000
  KAGGLE_BATCH_SIZE=500

Kaggle auth follows kagglehub/Kaggle defaults, for example ~/.kaggle/kaggle.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import kagglehub
import pandas as pd
from supabase import create_client


@dataclass(frozen=True)
class KaggleDataset:
    slug: str
    name: str
    source_url: str
    sport: str
    season_min: int | None = None
    season_max: int | None = None
    expected_files: tuple[str, ...] = ()
    notes: str = ""


DATASETS: tuple[KaggleDataset, ...] = (
    KaggleDataset(
        slug="christophertreasure/major-league-baseball-vegas-data",
        name="Major League Baseball Vegas Data",
        source_url="https://www.kaggle.com/datasets/christophertreasure/major-league-baseball-vegas-data",
        sport="MLB",
        season_min=2012,
        season_max=2021,
        expected_files=("oddsDataMLB.csv",),
        notes="MLB-specific historical Vegas/closing odds source.",
    ),
    KaggleDataset(
        slug="oliviersportsdata/us-sports-master-historical-closing-odds",
        name="US Sports Master Historical Closing Odds",
        source_url="https://www.kaggle.com/datasets/oliviersportsdata/us-sports-master-historical-closing-odds",
        sport="MLB",
        season_min=1998,
        season_max=2026,
        expected_files=("Sample_MLB_50rows.csv",),
        notes=(
            "Multi-sport historical closing odds archive. MLB sample exposes moneyline "
            "prices and final points; do not treat Number of Points - TOTAL as a bookmaker total line."
        ),
    ),
)


COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "country": ("Country", "country"),
    "season_label": ("Season", "season", "Season_Label"),
    "date": ("Date", "date", "Game_Date", "game_date"),
    "game_type": ("Type", "type", "Game_Type"),
    "home_team": ("Home_Team", "Home Team", "home_team", "Home"),
    "away_team": ("Away_Team", "Away Team", "away_team", "Away"),
    "home_points": ("Home_Points", "Home Points", "home_points", "Home_Score", "home_score"),
    "away_points": ("Away_Points", "Away Points", "away_points", "Away_Score", "away_score"),
    "odds_home": ("Odds_Home", "Home_Odds", "home_odds", "ML_Home"),
    "odds_away": ("Odds_Away", "Away_Odds", "away_odds", "ML_Away"),
    "end_of_rt": ("End_Of_RT", "End Of RT", "end_of_rt"),
    "total_points": ("Number of Points - TOTAL", "Total_Points", "total_points", "Total"),
    "winning_margin": ("Winning Margin", "Winning_Margin", "winning_margin"),
    "bookmaker": ("Bookmaker", "bookmaker", "book", "Book"),
    "market": ("Market", "market"),
}


def first_present(row: pd.Series, aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in row and pd.notna(row[alias]):
            return row[alias]
    return None


def to_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    try:
        return int(float(str(value).replace(",", "").strip()))
    except ValueError:
        return None


def to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def parse_date(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def parse_season(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None


def clean_raw_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def row_to_json(row: pd.Series) -> dict[str, Any]:
    return {str(key): clean_raw_value(value) for key, value in row.items()}


def infer_sport(dataset: KaggleDataset, row: pd.Series) -> str | None:
    season_label = first_present(row, COLUMN_ALIASES["season_label"])
    if season_label and "MLB" in str(season_label).upper():
        return "MLB"
    return dataset.sport


def build_raw_record(dataset: KaggleDataset, source_file: Path, row_number: int, row: pd.Series) -> dict[str, Any]:
    season_label = first_present(row, COLUMN_ALIASES["season_label"])
    raw_row = row_to_json(row)
    payload = {
        "dataset_slug": dataset.slug,
        "source_file": source_file.name,
        "source_row_number": row_number,
        "country": first_present(row, COLUMN_ALIASES["country"]),
        "season_label": season_label,
        "sport": infer_sport(dataset, row),
        "season": parse_season(season_label),
        "game_date": parse_date(first_present(row, COLUMN_ALIASES["date"])),
        "game_type": first_present(row, COLUMN_ALIASES["game_type"]),
        "home_team_raw": first_present(row, COLUMN_ALIASES["home_team"]),
        "away_team_raw": first_present(row, COLUMN_ALIASES["away_team"]),
        "home_points": to_int(first_present(row, COLUMN_ALIASES["home_points"])),
        "away_points": to_int(first_present(row, COLUMN_ALIASES["away_points"])),
        "odds_home": to_int(first_present(row, COLUMN_ALIASES["odds_home"])),
        "odds_away": to_int(first_present(row, COLUMN_ALIASES["odds_away"])),
        "end_of_rt": first_present(row, COLUMN_ALIASES["end_of_rt"]),
        "total_points": to_float(first_present(row, COLUMN_ALIASES["total_points"])),
        "winning_margin": first_present(row, COLUMN_ALIASES["winning_margin"]),
        "bookmaker_raw": first_present(row, COLUMN_ALIASES["bookmaker"]),
        "market_raw": first_present(row, COLUMN_ALIASES["market"]),
        "raw_row": raw_row,
        "normalization_status": "pending",
    }
    return {key: clean_raw_value(value) for key, value in payload.items()}


def stable_hash(record: dict[str, Any]) -> str:
    hash_input = json.dumps(
        {
            "dataset_slug": record.get("dataset_slug"),
            "source_file": record.get("source_file"),
            "source_row_number": record.get("source_row_number"),
            "raw_row": record.get("raw_row"),
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.md5(hash_input.encode("utf-8"), usedforsecurity=False).hexdigest()


def download_dataset(dataset: KaggleDataset) -> Path:
    return Path(kagglehub.dataset_download(dataset.slug))


def find_csv_files(dataset_path: Path, expected_files: tuple[str, ...]) -> list[Path]:
    csv_files = sorted(dataset_path.rglob("*.csv"))
    if not expected_files:
        return csv_files
    expected = {name.lower() for name in expected_files}
    preferred = [path for path in csv_files if path.name.lower() in expected]
    return preferred or csv_files


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def chunked(records: list[dict[str, Any]], size: int):
    for i in range(0, len(records), size):
        yield records[i : i + size]


def upsert_dataset(supabase, dataset: KaggleDataset, row_count: int) -> None:
    supabase.table("raw_kaggle_datasets").upsert(
        {
            "dataset_slug": dataset.slug,
            "dataset_name": dataset.name,
            "source_url": dataset.source_url,
            "sport": dataset.sport,
            "season_min": dataset.season_min,
            "season_max": dataset.season_max,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "row_count": row_count,
            "notes": dataset.notes,
        },
        on_conflict="dataset_slug",
    ).execute()


def insert_raw_records(supabase, records: list[dict[str, Any]], batch_size: int) -> int:
    inserted = 0
    seen_hashes: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for record in records:
        row_hash = stable_hash(record)
        if row_hash in seen_hashes:
            continue
        seen_hashes.add(row_hash)
        deduped.append(record)

    for batch in chunked(deduped, batch_size):
        supabase.table("raw_kaggle_odds").upsert(
            batch,
            on_conflict="dataset_slug,source_file,source_row_number",
        ).execute()
        inserted += len(batch)
    return inserted


def selected_datasets() -> list[KaggleDataset]:
    selected = os.getenv("KAGGLE_DATASETS")
    if not selected:
        return list(DATASETS)
    wanted = {item.strip() for item in selected.split(",") if item.strip()}
    return [dataset for dataset in DATASETS if dataset.slug in wanted]


def main() -> None:
    supabase_url = os.environ["SUPABASE_URL"]
    service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    max_rows = to_int(os.getenv("KAGGLE_MAX_ROWS"))
    batch_size = to_int(os.getenv("KAGGLE_BATCH_SIZE")) or 500
    supabase = create_client(supabase_url, service_key)

    for dataset in selected_datasets():
        print(f"Downloading {dataset.slug}...")
        dataset_path = download_dataset(dataset)
        csv_files = find_csv_files(dataset_path, dataset.expected_files)
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found for {dataset.slug} in {dataset_path}")

        total_rows = 0
        staged_rows = 0
        for csv_file in csv_files:
            print(f"Reading {csv_file}...")
            df = read_csv(csv_file)
            if max_rows is not None:
                df = df.head(max_rows)
            total_rows += len(df)
            records = [build_raw_record(dataset, csv_file, index + 1, row) for index, row in df.iterrows()]
            staged_rows += insert_raw_records(supabase, records, batch_size)
            print(f"Staged {len(records)} rows from {csv_file.name}.")

        upsert_dataset(supabase, dataset, total_rows)
        print(f"Completed {dataset.slug}: staged={staged_rows}, source_rows={total_rows}")


if __name__ == "__main__":
    main()
