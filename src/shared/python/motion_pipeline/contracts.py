"""Canonical Intermediate Representation (CIR) for the motion pipeline.

Pydantic v2 contracts shared by every stage of the markerless mocap to
motion-matching pipeline (epic #4558). Validators enforce DbC-style
invariants (monotonic timestamps, finite values, dimensional
consistency, acyclic parent indices, etc.).

This module has zero dependencies on engine, api, learning, apps,
tools, or deployment packages -- enforced by
``tests/unit/motion_pipeline/test_lod.py``.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UnitSystem(str, Enum):
    """Length unit system."""

    MILLIMETERS = "mm"
    METERS = "m"


class WorldUp(str, Enum):
    """World up-axis convention."""

    Y_UP = "Y_UP"
    Z_UP = "Z_UP"


class KeypointSchema(str, Enum):
    """Recognised 2D/3D keypoint topologies."""

    BODY_25 = "BODY_25"
    MEDIAPIPE_33 = "MEDIAPIPE_33"
    COCO_17 = "COCO_17"
    CUSTOM = "CUSTOM"


class EngineType(str, Enum):
    """Physics engines targetable by the motion pipeline.

    Lowercase string values match the convention used elsewhere in the
    codebase (see ``EngineManager``).
    """

    MUJOCO = "mujoco"
    OPENSIM = "opensim"
    DRAKE = "drake"
    PINOCCHIO = "pinocchio"
    MYOSUITE = "myosuite"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_finite(values: Any) -> bool:
    """Return True iff every scalar in ``values`` is finite."""
    if isinstance(values, bool):
        return True
    if isinstance(values, (int, float)):
        return math.isfinite(float(values))
    try:
        iterator = iter(values)
    except TypeError:
        return True
    return all(_all_finite(item) for item in iterator)


def _is_monotonic(timestamps: list[float]) -> bool:
    """Return True iff ``timestamps`` is non-decreasing."""
    return all(timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1))


_FROZEN = ConfigDict(frozen=True, arbitrary_types_allowed=False)


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


class Calibration(BaseModel):
    """Single-camera calibration.

    Multi-camera setups are represented as ``list[Calibration]`` by
    callers; each element is one camera with its own intrinsics /
    extrinsics. Intrinsics and extrinsics are optional so that purely
    monocular pipelines (without explicit calibration) can still flow
    through the CIR.
    """

    model_config = _FROZEN

    camera_id: str = Field(..., min_length=1)
    intrinsics: list[list[float]] | None = None
    extrinsics: list[list[float]] | None = None
    source_fps: float = Field(..., gt=0.0)
    unit_system: UnitSystem
    world_up: WorldUp

    @field_validator("intrinsics")
    @classmethod
    def _check_intrinsics(cls, v: list[list[float]] | None) -> list[list[float]] | None:
        if v is None:
            return v
        if len(v) != 3 or any(len(row) != 3 for row in v):
            raise ValueError("intrinsics must be a 3x3 matrix")
        if not _all_finite(v):
            raise ValueError("intrinsics entries must be finite")
        return v

    @field_validator("extrinsics")
    @classmethod
    def _check_extrinsics(cls, v: list[list[float]] | None) -> list[list[float]] | None:
        if v is None:
            return v
        if len(v) != 4 or any(len(row) != 4 for row in v):
            raise ValueError("extrinsics must be a 4x4 matrix")
        if not _all_finite(v):
            raise ValueError("extrinsics entries must be finite")
        return v


# ---------------------------------------------------------------------------
# Keypoints
# ---------------------------------------------------------------------------

PointTuple = tuple[float, float] | tuple[float, float, float]


class KeypointFrame(BaseModel):
    """Single frame of 2D or 3D keypoints with confidences."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    points: list[PointTuple]
    confidences: list[float]
    keypoint_schema: KeypointSchema = Field(..., alias="schema")
    timestamp: float

    @field_validator("timestamp")
    @classmethod
    def _finite_ts(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("timestamp must be finite")
        return v

    @field_validator("points")
    @classmethod
    def _check_points(cls, v: list[PointTuple]) -> list[PointTuple]:
        if not v:
            raise ValueError("points must be non-empty")
        dim = len(v[0])
        if dim not in (2, 3):
            raise ValueError("points must be 2D or 3D")
        for row in v:
            if len(row) != dim:
                raise ValueError("all keypoints must have the same dimensionality")
        if not _all_finite(v):
            raise ValueError("keypoint coordinates must be finite")
        return v

    @field_validator("confidences")
    @classmethod
    def _check_confidences(cls, v: list[float]) -> list[float]:
        if not _all_finite(v):
            raise ValueError("confidences must be finite")
        if any(c < 0.0 or c > 1.0 for c in v):
            raise ValueError("confidences must lie in [0, 1]")
        return v

    @model_validator(mode="after")
    def _consistency(self) -> KeypointFrame:
        if len(self.confidences) != len(self.points):
            raise ValueError("confidences length must equal number of points")
        return self


class KeypointSequence(BaseModel):
    """Time-ordered keypoint frames sharing a single schema."""

    model_config = _FROZEN

    frames: list[KeypointFrame] = Field(..., min_length=1)
    calibration: Calibration

    @model_validator(mode="after")
    def _check(self) -> KeypointSequence:
        timestamps = [f.timestamp for f in self.frames]
        if not _is_monotonic(timestamps):
            raise ValueError("frame timestamps must be monotonic non-decreasing")
        schemas = {f.keypoint_schema for f in self.frames}
        if len(schemas) != 1:
            raise ValueError("all frames must share the same schema")
        n_points = {len(f.points) for f in self.frames}
        if len(n_points) != 1:
            raise ValueError("all frames must have the same number of keypoints")
        return self


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------


class MarkerSample(BaseModel):
    """A single labelled 3D marker observation."""

    model_config = _FROZEN

    xyz: tuple[float, float, float]
    occluded: bool = False

    @model_validator(mode="after")
    def _check(self) -> MarkerSample:
        if not self.occluded and not _all_finite(self.xyz):
            raise ValueError("xyz must be finite unless the marker is marked occluded")
        return self


class MarkerFrame(BaseModel):
    """One timestamped frame of labelled markers."""

    model_config = _FROZEN

    samples: dict[str, MarkerSample]
    timestamp: float

    @field_validator("timestamp")
    @classmethod
    def _finite_ts(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("timestamp must be finite")
        return v

    @field_validator("samples")
    @classmethod
    def _non_empty(cls, v: dict[str, MarkerSample]) -> dict[str, MarkerSample]:
        if not v:
            raise ValueError("samples must be non-empty")
        return v


class MarkerTrajectory(BaseModel):
    """Time-ordered marker frames with a shared label set."""

    model_config = _FROZEN

    frames: list[MarkerFrame] = Field(..., min_length=1)
    unit_system: UnitSystem
    marker_set_name: str | None = None

    @model_validator(mode="after")
    def _check(self) -> MarkerTrajectory:
        timestamps = [f.timestamp for f in self.frames]
        if not _is_monotonic(timestamps):
            raise ValueError("frame timestamps must be monotonic non-decreasing")
        ref_labels = set(self.frames[0].samples.keys())
        for i, f in enumerate(self.frames[1:], start=1):
            if set(f.samples.keys()) != ref_labels:
                raise ValueError(f"frame {i} marker label set differs from frame 0")
        return self


# ---------------------------------------------------------------------------
# Skeleton rig
# ---------------------------------------------------------------------------


class JointAxis(BaseModel):
    """Rotation axis for a 1-DoF joint, stored as a unit 3-vector.

    For cardinal axes use ``JointAxis.from_cardinal("X" | "Y" | "Z")``.
    """

    model_config = _FROZEN

    vector: tuple[float, float, float]

    @field_validator("vector")
    @classmethod
    def _check_vector(cls, v: tuple[float, float, float]) -> tuple[float, float, float]:
        if not _all_finite(v):
            raise ValueError("axis vector components must be finite")
        norm = math.sqrt(sum(c * c for c in v))
        if norm == 0.0:
            raise ValueError("axis vector must be non-zero")
        if not math.isclose(norm, 1.0, abs_tol=1e-6):
            raise ValueError("axis vector must have unit norm")
        return v

    @classmethod
    def from_cardinal(cls, axis: Literal["X", "Y", "Z"]) -> JointAxis:
        """Construct a JointAxis aligned with a cardinal axis."""
        if axis == "X":
            return cls(vector=(1.0, 0.0, 0.0))
        if axis == "Y":
            return cls(vector=(0.0, 1.0, 0.0))
        if axis == "Z":
            return cls(vector=(0.0, 0.0, 1.0))
        raise ValueError(f"unknown cardinal axis: {axis}")


class JointLimit(BaseModel):
    """Inclusive [lo, hi] joint angle limit (radians)."""

    model_config = _FROZEN

    lo: float
    hi: float

    @model_validator(mode="after")
    def _check(self) -> JointLimit:
        if not (math.isfinite(self.lo) and math.isfinite(self.hi)):
            raise ValueError("joint limit bounds must be finite")
        if self.lo > self.hi:
            raise ValueError("lo must be <= hi")
        return self


class SkeletonRig(BaseModel):
    """Kinematic skeleton: joints, parents, T-pose offsets, axes, limits."""

    model_config = _FROZEN

    joint_names: list[str] = Field(..., min_length=1)
    parents: list[int]
    tpose_offsets: list[tuple[float, float, float]]
    axes: list[JointAxis]
    limits: list[JointLimit]
    semantic_labels: dict[str, str] = Field(default_factory=dict)
    end_effectors: list[str] = Field(default_factory=list)

    @property
    def n_joints(self) -> int:
        return len(self.joint_names)

    @field_validator("joint_names")
    @classmethod
    def _unique_names(cls, v: list[str]) -> list[str]:
        if any(not name for name in v):
            raise ValueError("joint names must be non-empty strings")
        if len(set(v)) != len(v):
            raise ValueError("joint_names must be unique")
        return v

    @model_validator(mode="after")
    def _check_topology(self) -> SkeletonRig:
        n = self.n_joints
        for length, label in (
            (len(self.parents), "parents"),
            (len(self.tpose_offsets), "tpose_offsets"),
            (len(self.axes), "axes"),
            (len(self.limits), "limits"),
        ):
            if length != n:
                raise ValueError(f"{label} length must equal n_joints ({n})")

        for offset in self.tpose_offsets:
            if not _all_finite(offset):
                raise ValueError("tpose_offsets must be finite")

        # Validate parent indices and detect cycles via DFS to root.
        for i, p in enumerate(self.parents):
            if p == i:
                raise ValueError(f"joint {i} cannot be its own parent")
            if not (-1 <= p < n):
                raise ValueError(
                    f"parent index {p} for joint {i} out of range [-1, {n - 1}]"
                )

        for start in range(n):
            seen: set[int] = set()
            cur = start
            while cur != -1:
                if cur in seen:
                    raise ValueError(f"cycle detected in parent chain at joint {cur}")
                seen.add(cur)
                cur = self.parents[cur]

        names = set(self.joint_names)
        for label, target in self.semantic_labels.items():
            if target not in names:
                raise ValueError(
                    f"semantic_labels['{label}']='{target}' not in joint_names"
                )
        for ee in self.end_effectors:
            if ee not in names:
                raise ValueError(f"end_effector '{ee}' not in joint_names")
        return self


# ---------------------------------------------------------------------------
# Joint trajectories
# ---------------------------------------------------------------------------


class JointStateFrame(BaseModel):
    """Generalised coordinates (and optional derivatives) at one timestamp."""

    model_config = _FROZEN

    q: list[float]
    qdot: list[float] | None = None
    qddot: list[float] | None = None
    timestamp: float

    @field_validator("timestamp")
    @classmethod
    def _finite_ts(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("timestamp must be finite")
        return v

    @field_validator("q")
    @classmethod
    def _check_q(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("q must be non-empty")
        if not _all_finite(v):
            raise ValueError("q values must be finite")
        return v

    @model_validator(mode="after")
    def _consistent_derivs(self) -> JointStateFrame:
        n = len(self.q)
        if self.qdot is not None:
            if len(self.qdot) != n:
                raise ValueError("qdot length must match q")
            if not _all_finite(self.qdot):
                raise ValueError("qdot values must be finite")
        if self.qddot is not None:
            if len(self.qddot) != n:
                raise ValueError("qddot length must match q")
            if not _all_finite(self.qddot):
                raise ValueError("qddot values must be finite")
        return self


class JointTrajectory(BaseModel):
    """Time-ordered joint states bound to a rig (1-DoF per joint)."""

    model_config = _FROZEN

    frames: list[JointStateFrame] = Field(..., min_length=1)
    rig: SkeletonRig

    @model_validator(mode="after")
    def _check(self) -> JointTrajectory:
        timestamps = [f.timestamp for f in self.frames]
        if not _is_monotonic(timestamps):
            raise ValueError("frame timestamps must be monotonic non-decreasing")
        n = self.rig.n_joints
        for i, f in enumerate(self.frames):
            if len(f.q) != n:
                raise ValueError(
                    f"frame {i}: q has {len(f.q)} entries, rig has {n} joints"
                )
        return self


# ---------------------------------------------------------------------------
# Provenance + headline CIR
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class Provenance(BaseModel):
    """Capture / source provenance for a motion artefact."""

    model_config = _FROZEN

    subject_id: str | None = None
    sport: str | None = "golf"
    club: str | None = None
    source_path_hash: str | None = None
    software_version: str
    created_at: datetime = Field(default_factory=_utc_now)


class MotionTrajectory(BaseModel):
    """Headline canonical intermediate representation."""

    model_config = _FROZEN

    rig: SkeletonRig
    joint_trajectory: JointTrajectory
    markers: MarkerTrajectory | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def _rigs_match(self) -> MotionTrajectory:
        if self.joint_trajectory.rig.joint_names != self.rig.joint_names:
            raise ValueError(
                "joint_trajectory.rig.joint_names must equal rig.joint_names"
            )
        return self


# ---------------------------------------------------------------------------
# Motion matching request / result
# ---------------------------------------------------------------------------


class CostWeights(BaseModel):
    """Non-negative weights for arbitrary cost terms."""

    model_config = _FROZEN

    weights: dict[str, float] = Field(default_factory=dict)

    @field_validator("weights")
    @classmethod
    def _non_negative(cls, v: dict[str, float]) -> dict[str, float]:
        for k, val in v.items():
            if not math.isfinite(val):
                raise ValueError(f"weight '{k}' must be finite")
            if val < 0.0:
                raise ValueError(f"weight '{k}' must be >= 0")
        return v


class MotionMatchingRequest(BaseModel):
    """Inputs to the motion-matching solver."""

    model_config = _FROZEN

    reference: MotionTrajectory
    cost_weights: CostWeights
    constraints: dict[str, Any] = Field(default_factory=dict)
    time_horizon: float | None = None
    integrator: dict[str, Any] = Field(default_factory=dict)
    engine: EngineType

    @field_validator("time_horizon")
    @classmethod
    def _positive_horizon(cls, v: float | None) -> float | None:
        if v is not None:
            if not math.isfinite(v):
                raise ValueError("time_horizon must be finite")
            if v <= 0.0:
                raise ValueError("time_horizon must be > 0 if given")
        return v


class TorqueTrajectory(BaseModel):
    """Joint-torque control trajectory."""

    model_config = _FROZEN

    frames: list[tuple[float, list[float]]] = Field(..., min_length=1)
    rig_joint_names: list[str] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _check(self) -> TorqueTrajectory:
        ts = [t for t, _ in self.frames]
        if not _is_monotonic(ts):
            raise ValueError("torque frame timestamps must be monotonic")
        n = len(self.rig_joint_names)
        for i, (t, vec) in enumerate(self.frames):
            if not math.isfinite(t):
                raise ValueError(f"torque frame {i}: timestamp not finite")
            if len(vec) != n:
                raise ValueError(
                    f"torque frame {i}: expected {n} entries, got {len(vec)}"
                )
            if not _all_finite(vec):
                raise ValueError(f"torque frame {i}: values not finite")
        return self


class MuscleActivationTrajectory(BaseModel):
    """Muscle-activation control trajectory (activations in [0, 1])."""

    model_config = _FROZEN

    frames: list[tuple[float, list[float]]] = Field(..., min_length=1)
    muscle_names: list[str] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _check(self) -> MuscleActivationTrajectory:
        if len(set(self.muscle_names)) != len(self.muscle_names):
            raise ValueError("muscle_names must be unique")
        ts = [t for t, _ in self.frames]
        if not _is_monotonic(ts):
            raise ValueError("muscle frame timestamps must be monotonic")
        n = len(self.muscle_names)
        for i, (t, vec) in enumerate(self.frames):
            if not math.isfinite(t):
                raise ValueError(f"muscle frame {i}: timestamp not finite")
            if len(vec) != n:
                raise ValueError(
                    f"muscle frame {i}: expected {n} activations, got {len(vec)}"
                )
            if not _all_finite(vec):
                raise ValueError(f"muscle frame {i}: values not finite")
            if any(a < 0.0 or a > 1.0 for a in vec):
                raise ValueError(f"muscle frame {i}: activations must lie in [0, 1]")
        return self


class ResidualReport(BaseModel):
    """Residual / fit summary."""

    model_config = _FROZEN

    per_joint_rmse: dict[str, float] = Field(default_factory=dict)
    aggregate_rmse: float = Field(..., ge=0.0)
    notes: str = ""

    @field_validator("per_joint_rmse")
    @classmethod
    def _non_neg_finite(cls, v: dict[str, float]) -> dict[str, float]:
        for k, val in v.items():
            if not math.isfinite(val) or val < 0.0:
                raise ValueError(f"per_joint_rmse['{k}']={val} must be finite and >= 0")
        return v

    @field_validator("aggregate_rmse")
    @classmethod
    def _finite_agg(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("aggregate_rmse must be finite")
        return v


class MotionMatchingResult(BaseModel):
    """Outputs of the motion-matching solver."""

    model_config = _FROZEN

    tracked: JointTrajectory
    torques: TorqueTrajectory | None = None
    activations: MuscleActivationTrajectory | None = None
    residuals: ResidualReport
    fit_metrics: dict[str, float] = Field(default_factory=dict)
    provenance: Provenance

    @model_validator(mode="after")
    def _at_least_one_control(self) -> MotionMatchingResult:
        if self.torques is None and self.activations is None:
            raise ValueError(
                "MotionMatchingResult requires at least one of torques / activations"
            )
        return self
