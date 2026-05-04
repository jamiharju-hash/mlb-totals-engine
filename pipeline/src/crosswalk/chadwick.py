"""Chadwick crosswalk resolver utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChadwickCrosswalk:
    """Minimal resolver for Retrosheet -> MLBAM IDs."""

    mapping: dict[str, int]

    def resolve_retro(self, retro_id: str | None) -> int | None:
        if not retro_id:
            return None
        return self.mapping.get(retro_id)


_CROSSWALK = ChadwickCrosswalk(mapping={})


def get_crosswalk() -> ChadwickCrosswalk:
    """Return singleton crosswalk resolver.

    Tests can monkeypatch this function or mutate the singleton mapping.
    """

    return _CROSSWALK
