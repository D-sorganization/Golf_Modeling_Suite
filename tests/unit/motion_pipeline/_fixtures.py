"""Synthetic fixture builders for motion-pipeline contract tests.

These helpers are reused by downstream waves of epic #4558 -- keep them
side-effect-free, deterministic, and minimal.
"""

from __future__ import annotations

import math

from src.shared.python.motion_pipeline import (
    Calibration,
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
    MotionTrajectory,
    Provenance,
    SkeletonRig,
    UnitSystem,
    WorldUp,
)


def make_calibration(
    camera_id: str = "cam0",
    fps: float = 60.0,
    unit_system: UnitSystem = UnitSystem.METERS,
    world_up: WorldUp = WorldUp.Y_UP,
) -> Calibration:
    return Calibration(
        camera_id=camera_id,
        intrinsics=[[1000.0, 0.0, 640.0], [0.0, 1000.0, 360.0], [0.0, 0.0, 1.0]],
        extrinsics=[
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        source_fps=fps,
        unit_system=unit_system,
        world_up=world_up,
    )


def make_keypoint_sequence(
    n_frames: int = 10,
    n_points: int = 33,
    schema: KeypointSchema = KeypointSchema.MEDIAPIPE_33,
    fps: float = 60.0,
) -> KeypointSequence:
    dt = 1.0 / fps
    frames = []
    for f in range(n_frames):
        points: list[tuple[float, float, float]] = [
            (
                math.cos(0.1 * (f + p)),
                math.sin(0.1 * (f + p)),
                0.5 * p / max(n_points, 1),
            )
            for p in range(n_points)
        ]
        confidences = [0.9 for _ in range(n_points)]
        frames.append(
            KeypointFrame(
                points=points,
                confidences=confidences,
                schema=schema,
                timestamp=f * dt,
            )
        )
    return KeypointSequence(frames=frames, calibration=make_calibration(fps=fps))


def make_marker_trajectory(
    n_frames: int = 10,
    marker_names: tuple[str, ...] = (
        "LSHO",
        "RSHO",
        "LASI",
        "RASI",
        "LKNE",
        "LANK",
    ),
    fps: float = 240.0,
    unit_system: UnitSystem = UnitSystem.METERS,
) -> MarkerTrajectory:
    dt = 1.0 / fps
    frames = []
    for f in range(n_frames):
        samples = {
            name: MarkerSample(
                xyz=(0.1 * i + 0.001 * f, 0.2 * i, 0.3 * i),
                occluded=False,
            )
            for i, name in enumerate(marker_names)
        }
        frames.append(MarkerFrame(samples=samples, timestamp=f * dt))
    return MarkerTrajectory(
        frames=frames,
        unit_system=unit_system,
        marker_set_name="synthetic",
    )


def make_skeleton_rig(n_joints: int = 6) -> SkeletonRig:
    if n_joints < 1:
        raise ValueError("n_joints must be >= 1")
    joint_names = [f"joint_{i}" for i in range(n_joints)]
    parents = [-1] + list(range(n_joints - 1))  # simple chain
    tpose_offsets = [(0.0, float(i) * 0.1, 0.0) for i in range(n_joints)]
    axes = [JointAxis.from_cardinal("Z") for _ in range(n_joints)]
    limits = [JointLimit(lo=-math.pi, hi=math.pi) for _ in range(n_joints)]
    semantic_labels = {"root": joint_names[0]}
    end_effectors = [joint_names[-1]]
    return SkeletonRig(
        joint_names=joint_names,
        parents=parents,
        tpose_offsets=tpose_offsets,
        axes=axes,
        limits=limits,
        semantic_labels=semantic_labels,
        end_effectors=end_effectors,
    )


def make_joint_trajectory(
    rig: SkeletonRig,
    n_frames: int = 10,
    fps: float = 240.0,
) -> JointTrajectory:
    dt = 1.0 / fps
    frames = [
        JointStateFrame(
            q=[0.01 * (i + f) for i in range(rig.n_joints)],
            qdot=[0.0 for _ in range(rig.n_joints)],
            qddot=None,
            timestamp=f * dt,
        )
        for f in range(n_frames)
    ]
    return JointTrajectory(frames=frames, rig=rig)


def make_provenance(software_version: str = "0.1.0") -> Provenance:
    return Provenance(
        subject_id="subject_001",
        sport="golf",
        club="7iron",
        source_path_hash="deadbeef",
        software_version=software_version,
    )


def make_motion_trajectory(
    n_joints: int = 6,
    n_frames: int = 10,
) -> MotionTrajectory:
    rig = make_skeleton_rig(n_joints=n_joints)
    jt = make_joint_trajectory(rig, n_frames=n_frames)
    mt = make_marker_trajectory(n_frames=n_frames)
    prov = make_provenance()
    return MotionTrajectory(
        rig=rig,
        joint_trajectory=jt,
        markers=mt,
        provenance=prov,
    )
