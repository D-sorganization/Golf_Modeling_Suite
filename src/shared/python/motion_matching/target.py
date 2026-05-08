"""Public re-export of the ``ClubTarget`` and ``ClubBallTarget`` dataclasses.

Issue #4095 promotes the loader/oracle/cost surface to a top-level package.
``target`` is the canonical module name (matching ``target.m`` in MATLAB
conceptual layout); historical code imports from ``club_target`` and that
import path is preserved.

Public API:
    ClubTarget       -- frozen dataclass for a measured club swing.
    AlignOptions     -- resampling and impact-alignment options.
    SourceProvenance -- file-level provenance metadata.
    BallImpactState  -- frozen dataclass for ball state at impact.
    ClubBallTarget   -- composite ``ClubTarget`` + ``BallImpactState``.
    extract_ball_impact_from_clubtarget -- approximate ball-impact extractor.
"""

from __future__ import annotations

from .club_ball_target import (
    BallImpactState,
    ClubBallTarget,
    extract_ball_impact_from_clubtarget,
)
from .club_target import (
    QUAT_NORM_TOL,
    TIME_EPS,
    AlignOptions,
    ClubTarget,
    SourceProvenance,
    ValidAlignment,
)

__all__ = [
    "AlignOptions",
    "BallImpactState",
    "ClubBallTarget",
    "ClubTarget",
    "QUAT_NORM_TOL",
    "SourceProvenance",
    "TIME_EPS",
    "ValidAlignment",
    "extract_ball_impact_from_clubtarget",
]
