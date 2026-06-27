"""Engine-class baseline library transmuted from the VED reference engines.

The two VED slices are no longer display vehicles; their telemetry defines the
healthy bands the distance measure scores real drives against. A drive is matched
to the nearest engine class by displacement, and the VED-derived band for that
class replaces the manual engine-load band.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_PROFILE_PATH = Path(__file__).resolve().parents[3] / "data" / "ved_baseline_profiles.json"

# Manual fallback band (used only if the VED profile file is missing/incomplete).
_FALLBACK_ENGINE_LOAD = (12.0, 35.0)
_HEAVY_DISPLACEMENT_L = 3.0
_HEAVY_CYL = re.compile(r"\bV(?:6|8|10|12)\b", re.IGNORECASE)
_DISPLACEMENT = re.compile(r"(\d+(?:\.\d+)?)\s*L", re.IGNORECASE)


def engine_class(engine: str | None) -> str:
    """Return 'heavy' for large-displacement / multi-bank engines, else 'light'."""
    if not engine:
        return "light"
    if _HEAVY_CYL.search(engine):
        return "heavy"
    match = _DISPLACEMENT.search(engine)
    if match and float(match.group(1)) >= _HEAVY_DISPLACEMENT_L:
        return "heavy"
    return "light"


@lru_cache(maxsize=1)
def _profiles() -> dict:
    try:
        return json.loads(_PROFILE_PATH.read_text()).get("profiles", {})
    except (OSError, ValueError):
        return {}


def engine_load_band(engine: str | None) -> tuple[float, float]:
    """VED-derived healthy engine-load band for this engine's class."""
    cls = engine_class(engine)
    band = _profiles().get(cls, {}).get("engine_load_pct")
    if band and "healthy_min" in band and "healthy_max" in band:
        return (float(band["healthy_min"]), float(band["healthy_max"]))
    return _FALLBACK_ENGINE_LOAD


def baseline_source(engine: str | None) -> str:
    return f"ved-{engine_class(engine)}" if _profiles() else "manual"
