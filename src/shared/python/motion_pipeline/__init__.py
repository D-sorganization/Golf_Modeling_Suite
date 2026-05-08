"""Motion pipeline canonical intermediate representation (CIR).

Pydantic v2 contracts for the markerless mocap to motion-matching
pipeline. This package is the foundation of epic #4558 -- every later
stage depends on these types. It must not import from engines, api,
learning, apps, tools, or deployment (Law of Demeter at the package
level).
"""

from src.shared.python.motion_pipeline.contracts import (
    Calibration,
    CostWeights,
    EngineType,
    JointAxis,
    JointLimit,
    JointStateFrame,
    JointTrajectory,
    KeypointFrame,
    KeypointSchema,
    KeypointSequence,
    MarkerFrame,
    MarkerSample,
    MarkerTrajectory,
    MotionMatchingRequest,
    MotionMatchingResult,
    MotionTrajectory,
    MuscleActivationTrajectory,
    Provenance,
    ResidualReport,
    SkeletonRig,
    TorqueTrajectory,
    UnitSystem,
    WorldUp,
)

__all__ = [
    "Calibration",
    "CostWeights",
    "EngineType",
    "JointAxis",
    "JointLimit",
    "JointStateFrame",
    "JointTrajectory",
    "KeypointFrame",
    "KeypointSchema",
    "KeypointSequence",
    "MarkerFrame",
    "MarkerSample",
    "MarkerTrajectory",
    "MotionMatchingRequest",
    "MotionMatchingResult",
    "MotionTrajectory",
    "MuscleActivationTrajectory",
    "Provenance",
    "ResidualReport",
    "SkeletonRig",
    "TorqueTrajectory",
    "UnitSystem",
    "WorldUp",
]
