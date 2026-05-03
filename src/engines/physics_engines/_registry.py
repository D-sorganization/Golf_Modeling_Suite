"""Engine tier registry.

Reads all ``_tier.py`` metadata files from each engine sub-package and
exposes a single :data:`TIER_REGISTRY` mapping so callers can inspect the
tier, description, install extra, and any experimental warnings without
importing the engines themselves.
"""

import importlib
from typing import Any

_ENGINES = ["mujoco", "drake", "pinocchio", "opensim", "myosuite"]

TIER_REGISTRY: dict[str, dict[str, Any]] = {}

for _engine in _ENGINES:
    _mod = importlib.import_module(f"src.engines.physics_engines.{_engine}._tier")
    _entry: dict[str, Any] = {
        "tier": _mod.TIER,
        "description": _mod.DESCRIPTION,
        "install_extra": _mod.INSTALL_EXTRA,
    }
    if hasattr(_mod, "WARNING"):
        _entry["WARNING"] = _mod.WARNING
    TIER_REGISTRY[_engine] = _entry
