from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

SCHEMA_VERSION = "1.0"

BIOMECHANICAL_MARKER_MIN_M = 0.001
BIOMECHANICAL_MARKER_MAX_M = 10.0


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
