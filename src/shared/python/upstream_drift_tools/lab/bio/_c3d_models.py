from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

SCHEMA_VERSION = "1.0"

BIOMECHANICAL_MARKER_MIN_M = 0.001
BIOMECHANICAL_MARKER_MAX_M = 10.0


class MarkerSet(Enum):
    """Known marker set configurations for C3D files.

    Members:
        CGM2_4: CGM2.4 marker set (typically ~39 markers)
        PLUG_IN_GAIT_41: Vicon Plug-in-Gait 41-marker set
        IOR: Institute of Orthopaedic Research marker set
        GOLF_CLUSTER: Golf-specific marker cluster set
        UNKNOWN: Unrecognized marker set
    """

    CGM2_4 = "CGM2.4"
    PLUG_IN_GAIT_41 = "PLUG_IN_GAIT_41"
    IOR = "IOR"
    GOLF_CLUSTER = "GOLF_CLUSTER"
    UNKNOWN = "UNKNOWN"


# Marker name signatures for each known set
_MARKER_SET_SIGNATURES: dict[MarkerSet, set[str]] = {
    MarkerSet.CGM2_4: {
        "RASI", "LASI", "RPSI", "LPSI", "RSHO", "LSHO", "RELB", "LELB",
        "RWRB", "LWRB", "RFIN", "LFIN", "RTHI", "LTHI", "RKNE", "LKNE",
        "RTIB", "LTIB", "RANK", "LANK", "RHEE", "LHEE", "RTOE", "LTOE",
        "C7", "T10", "CLAV", "STRN", "RBHD", "LBHD", "RFHD", "LFHD",
    },
    MarkerSet.PLUG_IN_GAIT_41: {
        "RFHD", "LFHD", "LBHD", "RBHD", "C7", "T10", "CLAV", "STRN",
        "RSHO", "LSHO", "RUPA", "LUPA", "RELB", "LELB", "RFRM", "LFRM",
        "RWRB", "LWRB", "RWRM", "LWRM", "RFIN", "LFIN", "RTHI", "LTHI",
        "RKNE", "LKNE", "RTIB", "LTIB", "RANK", "LANK", "RHEE", "LHEE",
        "RTOE", "LTOE", "RPSI", "LPSI", "RASI", "LASI", "RKNM", "LKNM",
        "RANKM", "LANKM",
    },
    MarkerSet.IOR: {
        "SACR", "RASI", "LASI", "RTHI", "LTHI", "RKNE", "LKNE", "RTIB",
        "LTIB", "RANK", "LANK", "RHEE", "LHEE", "RTOE", "LTOE", "L5",
        "T12", "T8", "T1", "C7", "CLAV", "STRN", "JUG", "RBHD", "LBHD",
    },
    MarkerSet.GOLF_CLUSTER: {
        "hub", "spine", "torso", "ls", "rs", "le", "re", "lw", "rw",
        "mp", "ch", "hip",
    },
}


class MarkerSetMismatchError(Exception):
    """Raised when a C3D file's marker set does not match expected configurations."""

    pass


def detect_marker_set(
    marker_labels: list[str],
    override: MarkerSet | None = None,
) -> MarkerSet:
    """Detect the marker set from a list of marker labels.

    Uses a deterministic priority order based on signature matching:
    1. PLUG_IN_GAIT_41 (most specific, 41 markers)
    2. CGM2_4 (common clinical standard)
    3. IOR (research standard)
    4. GOLF_CLUSTER (domain-specific)
    5. UNKNOWN (fallback)

    Args:
        marker_labels: List of marker names from the C3D file.
        override: If provided, skip detection and return this value.

    Returns:
        The detected MarkerSet enum value.

    Raises:
        MarkerSetMismatchError: If detection yields UNKNOWN and no override
            was provided.
    """
    if override is not None:
        return override

    marker_set = set(marker_labels)

    # Priority-ordered detection
    for candidate, signature in [
        (MarkerSet.PLUG_IN_GAIT_41, _MARKER_SET_SIGNATURES[MarkerSet.PLUG_IN_GAIT_41]),
        (MarkerSet.CGM2_4, _MARKER_SET_SIGNATURES[MarkerSet.CGM2_4]),
        (MarkerSet.IOR, _MARKER_SET_SIGNATURES[MarkerSet.IOR]),
        (MarkerSet.GOLF_CLUSTER, _MARKER_SET_SIGNATURES[MarkerSet.GOLF_CLUSTER]),
    ]:
        # Require at least 80% of signature markers to match
        required_match = int(len(signature) * 0.8)
        matched = len(marker_set & signature)
        if matched >= required_match:
            return candidate

    result = MarkerSet.UNKNOWN
    if result is MarkerSet.UNKNOWN and override is None:
        raise MarkerSetMismatchError(
            f"Unrecognized marker set. Markers found: {sorted(marker_labels)}\n"
            f"Known sets: {[ms.value for ms in MarkerSet if ms != MarkerSet.UNKNOWN]}\n"
            "Pass override=MarkerSet.GOLF_CLUSTER or another known set to proceed."
        )
    return result


@dataclass(frozen=True)
class C3DEvent:
    """A labeled event occurring at a specific time within a capture."""

    label: str
    time: float

    def __post_init__(self) -> None:
        """Validate event data."""
        if not self.label:
            raise ValueError("Event label cannot be empty.")


@dataclass(frozen=True)
class ForcePlateCalibration:
    """Calibration data for a force plate from C3D FORCE_PLATFORM parameters.

    Attributes:
        plate_number: Plate number (1-indexed).
        type: Force plate type (1=force-only, 2=force+moment, 3=6-axis, 4=multi-6-axis).
        corners: 4x3 array of corner positions in lab frame [m].
        origin: 3D origin position [m].
        cal_matrix: Calibration matrix (shape varies by plate type).
        channel_indices: List of (start, end) channel index ranges for this plate.
    """

    plate_number: int
    type: int
    corners: np.ndarray | None = None
    origin: np.ndarray | None = None
    cal_matrix: np.ndarray | None = None
    channel_indices: list[tuple[int, int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate force plate calibration data."""
        if not 1 <= self.type <= 4:
            raise ValueError(f"Force plate type must be 1-4, got {self.type}")
        if self.corners is not None and self.corners.shape != (4, 3):
            raise ValueError(f"Corners must be 4x3, got {self.corners.shape}")
        if self.origin is not None and self.origin.shape != (3,):
            raise ValueError(f"Origin must be length 3, got {self.origin.shape}")


@dataclass(frozen=True)
class C3DMetadata:
    """Describes key properties of a C3D motion-capture recording."""

    marker_labels: list[str]
    frame_count: int
    frame_rate: float
    units: str
    analog_labels: list[str]
    analog_units: list[str]
    analog_rate: float | None
    events: list[C3DEvent]
    force_plates: list[ForcePlateCalibration] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate metadata fields."""
        if self.frame_count < 0:
            raise ValueError(f"Frame count cannot be negative: {self.frame_count}")
        if self.frame_rate < 0:
            raise ValueError(f"Frame rate cannot be negative: {self.frame_rate}")
        if self.analog_rate is not None and self.analog_rate < 0:
            raise ValueError(f"Analog rate cannot be negative: {self.analog_rate}")

        if len(self.analog_units) != len(self.analog_labels):
            raise ValueError(
                "analog_units and analog_labels must have the same length: "
                f"{len(self.analog_units)} units vs {len(self.analog_labels)} labels"
            )

    @property
    def marker_count(self) -> int:
        """Number of tracked markers in the recording."""

        return len(self.marker_labels)

    @property
    def analog_count(self) -> int:
        """Number of analog channels in the recording."""

        return len(self.analog_labels)

    @property
    def force_plate_count(self) -> int:
        """Number of force plates with calibration data."""
        return len(self.force_plates)

    @property
    def duration(self) -> float:
        """Capture duration in seconds, or ``0`` if the rate is missing."""

        if self.frame_rate == 0:
            return 0.0
        return self.frame_count / self.frame_rate
