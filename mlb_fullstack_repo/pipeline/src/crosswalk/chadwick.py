from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import requests

from src.config import RAW_DIR

LOGGER = logging.getLogger(__name__)

CHADWICK_REGISTER_URL = "https://github.com/chadwickbureau/register/raw/master/data/people.csv"
CHADWICK_CACHE_PATH = RAW_DIR / "chadwick_register.csv"
CACHE_MAX_AGE_DAYS = 7


class QualityCheckError(RuntimeError):
    """Raised when chadwick crosswalk quality checks fail."""


@dataclass(frozen=True)
class PlayerIdentity:
    key_mlbam: int | None
    key_retro: str | None
    key_bbref: str | None
    key_fangraphs: str | None
    key_uuid: str | None
    name_first: str | None
    name_last: str | None


class CrosswalkIndex:
    def __init__(self, rows: Iterable[dict[str, str]]):
        self._by_mlbam: dict[int, PlayerIdentity] = {}
        self._by_retro: dict[str, PlayerIdentity] = {}
        self._by_lahman: dict[str, PlayerIdentity] = {}
        self._by_bbref: dict[str, PlayerIdentity] = {}
        self._build(rows)

    def _build(self, rows: Iterable[dict[str, str]]) -> None:
        seen_mlbam: set[int] = set()
        seen_retro: set[str] = set()
        seen_bbref: set[str] = set()

        for row in rows:
            player = PlayerIdentity(
                key_mlbam=_to_int_or_none(row.get("key_mlbam")),
                key_retro=_to_str_or_none(row.get("key_retro")),
                key_bbref=_to_str_or_none(row.get("key_bbref")),
                key_fangraphs=_to_str_or_none(row.get("key_fangraphs")),
                key_uuid=_to_str_or_none(row.get("key_uuid")),
                name_first=_to_str_or_none(row.get("name_first")),
                name_last=_to_str_or_none(row.get("name_last")),
            )
            lahman_id = _to_str_or_none(row.get("key_lahman"))

            if player.key_mlbam is not None:
                if player.key_mlbam in seen_mlbam:
                    raise QualityCheckError(f"Duplicate key_mlbam: {player.key_mlbam}")
                seen_mlbam.add(player.key_mlbam)
                self._by_mlbam[player.key_mlbam] = player

            if player.key_retro is not None:
                if player.key_retro in seen_retro:
                    raise QualityCheckError(f"Duplicate key_retro: {player.key_retro}")
                seen_retro.add(player.key_retro)
                self._by_retro[player.key_retro] = player

            if player.key_bbref is not None:
                if player.key_bbref in seen_bbref:
                    raise QualityCheckError(f"Duplicate key_bbref: {player.key_bbref}")
                seen_bbref.add(player.key_bbref)
                self._by_bbref[player.key_bbref] = player

            if lahman_id is not None:
                self._by_lahman[lahman_id] = player

    def resolve_mlbam(self, mlbam_id: int) -> PlayerIdentity | None:
        return self._by_mlbam.get(mlbam_id)

    def resolve_retro(self, retro_id: str) -> PlayerIdentity | None:
        return self._by_retro.get(retro_id)

    def resolve_lahman(self, lahman_id: str) -> PlayerIdentity | None:
        return self._by_lahman.get(lahman_id)

    def resolve_bbref(self, bbref_id: str) -> PlayerIdentity | None:
        return self._by_bbref.get(bbref_id)

    def check_coverage(self, provided_ids: Iterable[str | int], id_type: str) -> float:
        provided = list(provided_ids)
        if not provided:
            return 1.0

        resolver = {
            "mlbam": lambda x: self.resolve_mlbam(int(x)),
            "retro": lambda x: self.resolve_retro(str(x)),
            "lahman": lambda x: self.resolve_lahman(str(x)),
            "bbref": lambda x: self.resolve_bbref(str(x)),
        }.get(id_type)

        if resolver is None:
            raise ValueError(f"Unsupported id_type for coverage: {id_type}")

        resolved = sum(1 for source_id in provided if resolver(source_id) is not None)
        coverage = resolved / len(provided)
        if coverage < 0.995:
            LOGGER.warning("Crosswalk coverage SLO warning: %.2f%% for %s", coverage * 100, id_type)
        return coverage


def ensure_chadwick_register(path: Path = CHADWICK_CACHE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if datetime.now(timezone.utc) - modified_at < timedelta(days=CACHE_MAX_AGE_DAYS):
            return path

    response = requests.get(CHADWICK_REGISTER_URL, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def load_chadwick_rows(path: Path = CHADWICK_CACHE_PATH) -> list[dict[str, str]]:
    csv_path = ensure_chadwick_register(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_unresolvable_to_quarantine(
    *,
    source: str,
    source_id: str,
    source_id_type: str,
    player_name: str | None,
    context: dict[str, str] | None = None,
) -> None:
    supabase_url = os.getenv("SUPABASE_URL", "")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not service_key:
        LOGGER.warning("Unable to write unresolved id to quarantine table; Supabase credentials not configured")
        return

    payload = {
        "source": source,
        "source_id": source_id,
        "source_id_type": source_id_type,
        "player_name": player_name,
        "context": context or {},
    }
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    response = requests.post(f"{supabase_url}/rest/v1/player_crosswalk_quarantine", json=payload, headers=headers, timeout=30)
    response.raise_for_status()


_CROSSWALK_SINGLETON: CrosswalkIndex | None = None


def get_crosswalk() -> CrosswalkIndex:
    global _CROSSWALK_SINGLETON
    if _CROSSWALK_SINGLETON is None:
        _CROSSWALK_SINGLETON = CrosswalkIndex(load_chadwick_rows())
    return _CROSSWALK_SINGLETON


def _to_int_or_none(value: str | None) -> int | None:
    stripped = _to_str_or_none(value)
    return int(stripped) if stripped is not None else None


def _to_str_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
