import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from src.crosswalk.chadwick import CrosswalkIndex, QualityCheckError


@pytest.fixture
def sample_rows() -> list[dict[str, str]]:
    return [
        {
            "key_mlbam": "545361",
            "key_retro": "troum001",
            "key_bbref": "troutmi01",
            "key_fangraphs": "10155",
            "key_uuid": "uuid-trout",
            "name_first": "Mike",
            "name_last": "Trout",
            "key_lahman": "troutmi01",
        },
        {
            "key_mlbam": "123456",
            "key_retro": "doejo001",
            "key_bbref": "doejo01",
            "key_fangraphs": "99999",
            "key_uuid": "uuid-doe",
            "name_first": "John",
            "name_last": "Doe",
            "key_lahman": "doejo01",
        },
    ]


def test_resolve_mlbam_returns_identity(sample_rows: list[dict[str, str]]) -> None:
    index = CrosswalkIndex(sample_rows)
    player = index.resolve_mlbam(545361)
    assert player is not None
    assert player.name_first == "Mike"
    assert player.name_last == "Trout"
    assert player.key_bbref == "troutmi01"


def test_resolve_retro_returns_identity(sample_rows: list[dict[str, str]]) -> None:
    index = CrosswalkIndex(sample_rows)
    player = index.resolve_retro("troum001")
    assert player is not None
    assert player.key_mlbam == 545361


def test_unresolvable_id_returns_none(sample_rows: list[dict[str, str]]) -> None:
    index = CrosswalkIndex(sample_rows)
    assert index.resolve_mlbam(999999999) is None


def test_duplicate_detection_raises_quality_check_error(sample_rows: list[dict[str, str]]) -> None:
    duplicated = sample_rows + [{**sample_rows[0], "key_uuid": "new-uuid"}]
    with pytest.raises(QualityCheckError):
        CrosswalkIndex(duplicated)
