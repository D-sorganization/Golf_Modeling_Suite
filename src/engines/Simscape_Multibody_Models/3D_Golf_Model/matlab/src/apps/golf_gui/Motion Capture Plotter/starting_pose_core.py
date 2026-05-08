"""DEPRECATED — relocated to ``src.tools.starting_pose_matcher.core``.

This shim re-exports the new public API so any sibling code or test
fixture that still imports ``starting_pose_core`` from this directory
keeps working through one release cycle.  See issue #4376.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "starting_pose_core at this path is deprecated.  Import from "
    "``src.tools.starting_pose_matcher.core`` instead.  See issue #4376.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export the new core's public surface unchanged.
from src.tools.starting_pose_matcher.core import (  # noqa: E402, F401
    CM_TO_M,
    DEFAULT_EVENT_PRESET,
    DEFAULT_PHASE,
    EVENT_KEYS,
    EVENT_LABEL_PRESETS,
    FALLBACK_SEGMENTS,
    MocapEvents,
    PHASE_BOUNDS,
    PHASE_KEYS,
    PHASE_LEGACY_LABELS,
    PoseSlot,
    RigidTransform,
    SESSION_SCHEMA_VERSION,
    Skeleton,
    SkeletonTrajectory,
    fallback_skeleton,
    load_mocap_xlsx,
    load_simscape_trajectory_csv,
    load_skeleton,
    phase_display_label,
    phase_key_from_label,
    read_event_header,
    solve_shaft_rz_deg,
)

# Legacy-compat dict aliases — older code occasionally referenced these
# constants directly.  Keep them around as derived dicts.
def _legacy_fallback_dict(pose_name: str) -> dict[str, list[float]]:
    skel = fallback_skeleton(pose_name)
    return {k: v.tolist() for k, v in skel.joints.items()}


FALLBACK_IMPACT = _legacy_fallback_dict("Impact")
FALLBACK_TOB = _legacy_fallback_dict("TopofBackswing")
