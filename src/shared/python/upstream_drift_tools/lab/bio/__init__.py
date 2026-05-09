"""Bio/Lab - Biomechanics data readers and laboratory tools.

Modules:
    c3d_reader: C3D motion capture file reader with event and metadata parsing
    marker_sets: Deterministic marker-set detection (Plug-in-Gait, CGM2.4, IOR,
        custom golf-cluster) with INFO-level logging of the chosen set.
"""

from ._c3d_models import MarkerSetMismatchError
from .c3d_reader import C3DDataReader, C3DEvent, C3DMetadata
from .marker_sets import (
    CANONICAL_LABELS,
    DETECTION_PRIORITY,
    REQUIRED_LABELS,
    MarkerSet,
    detect_marker_set,
    missing_required,
)

__all__ = [
    "CANONICAL_LABELS",
    "C3DDataReader",
    "C3DEvent",
    "C3DMetadata",
    "DETECTION_PRIORITY",
    "MarkerSet",
    "MarkerSetMismatchError",
    "REQUIRED_LABELS",
    "detect_marker_set",
    "missing_required",
]
