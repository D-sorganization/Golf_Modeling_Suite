"""Unit tests for the motion pipeline canonical intermediate representation.

Targets >=95% coverage of ``src/shared/python/motion_pipeline/contracts.py``.
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from src.shared.python.motion_pipeline import (
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
from tests.unit.motion_pipeline._fixtures import (
    make_calibration,
    make_joint_trajectory,
    make_keypoint_sequence,
    make_marker_trajectory,
    make_motion_trajectory,
    make_provenance,
    make_skeleton_rig,
)


# ---------------------------------------------------------------------------
# Enums + simple sanity
# ---------------------------------------------------------------------------


def test_engine_type_lowercase_string_values() -> None:
    assert EngineType.MUJOCO.value == "mujoco"
    assert EngineType.OPENSIM.value == "opensim"
    assert EngineType.DRAKE.value == "drake"
    assert EngineType.PINOCCHIO.value == "pinocchio"
    assert EngineType.MYOSUITE.value == "myosuite"


def test_unit_system_world_up_keypoint_schema_values() -> None:
    assert UnitSystem.MILLIMETERS.value == "mm"
    assert UnitSystem.METERS.value == "m"
    assert WorldUp.Y_UP.value == "Y_UP"
    assert WorldUp.Z_UP.value == "Z_UP"
    assert KeypointSchema.MEDIAPIPE_33.value == "MEDIAPIPE_33"


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def test_calibration_valid() -> None:
    c = make_calibration()
    assert c.source_fps == 60.0
    assert c.unit_system == UnitSystem.METERS


def test_calibration_minimal_no_optional_matrices() -> None:
    c = Calibration(
        camera_id="cam0",
        source_fps=30.0,
        unit_system=UnitSystem.MILLIMETERS,
        world_up=WorldUp.Z_UP,
    )
    assert c.intrinsics is None
    assert c.extrinsics is None


@pytest.mark.parametrize("bad", [[[1.0, 0.0]], [[1.0, 0.0, 0.0], [0.0]]])
def test_calibration_rejects_bad_intrinsics_shape(
    bad: list[list[float]],
) -> None:
    with pytest.raises(ValidationError):
        Calibration(
            camera_id="cam0",
            intrinsics=bad,
            source_fps=30.0,
            unit_system=UnitSystem.METERS,
            world_up=WorldUp.Y_UP,
        )


def test_calibration_rejects_non_finite_intrinsics() -> None:
    with pytest.raises(ValidationError):
        Calibration(
            camera_id="cam0",
            intrinsics=[
                [math.nan, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            source_fps=30.0,
            unit_system=UnitSystem.METERS,
            world_up=WorldUp.Y_UP,
        )


def test_calibration_rejects_bad_extrinsics_shape() -> None:
    with pytest.raises(ValidationError):
        Calibration(
            camera_id="cam0",
            extrinsics=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            source_fps=30.0,
            unit_system=UnitSystem.METERS,
            world_up=WorldUp.Y_UP,
        )


def test_calibration_rejects_zero_or_negative_fps() -> None:
    with pytest.raises(ValidationError):
        Calibration(
            camera_id="cam0",
            source_fps=0.0,
            unit_system=UnitSystem.METERS,
            world_up=WorldUp.Y_UP,
        )


# ---------------------------------------------------------------------------
# KeypointFrame / KeypointSequence
# ---------------------------------------------------------------------------


def test_keypoint_frame_valid_2d_and_3d() -> None:
    f2 = KeypointFrame(
        points=[(0.0, 0.0), (1.0, 1.0)],
        confidences=[0.5, 0.9],
        schema=KeypointSchema.CUSTOM,
        timestamp=0.0,
    )
    assert len(f2.points) == 2
    f3 = KeypointFrame(
        points=[(0.0, 0.0, 0.0)],
        confidences=[0.7],
        schema=KeypointSchema.CUSTOM,
        timestamp=0.0,
    )
    assert len(f3.points[0]) == 3


def test_keypoint_frame_rejects_confidence_length_mismatch() -> None:
    with pytest.raises(ValidationError):
        KeypointFrame(
            points=[(0.0, 0.0), (1.0, 1.0)],
            confidences=[0.5],
            schema=KeypointSchema.CUSTOM,
            timestamp=0.0,
        )


@pytest.mark.parametrize("bad", [-0.01, 1.5, math.inf, math.nan])
def test_keypoint_frame_rejects_invalid_confidence(bad: float) -> None:
    with pytest.raises(ValidationError):
        KeypointFrame(
            points=[(0.0, 0.0)],
            confidences=[bad],
            schema=KeypointSchema.CUSTOM,
            timestamp=0.0,
        )


def test_keypoint_frame_rejects_non_finite_points() -> None:
    with pytest.raises(ValidationError):
        KeypointFrame(
            points=[(math.inf, 0.0)],
            confidences=[1.0],
            schema=KeypointSchema.CUSTOM,
            timestamp=0.0,
        )


def test_keypoint_frame_rejects_mixed_dimensionality() -> None:
    with pytest.raises(ValidationError):
        KeypointFrame(
            points=[(0.0, 0.0), (1.0, 1.0, 1.0)],  # type: ignore[list-item]
            confidences=[1.0, 1.0],
            schema=KeypointSchema.CUSTOM,
            timestamp=0.0,
        )


def test_keypoint_sequence_valid() -> None:
    seq = make_keypoint_sequence(n_frames=4, n_points=5, schema=KeypointSchema.CUSTOM)
    assert len(seq.frames) == 4


def test_keypoint_sequence_rejects_non_monotonic_timestamps() -> None:
    cal = make_calibration()
    f0 = KeypointFrame(
        points=[(0.0, 0.0)],
        confidences=[1.0],
        schema=KeypointSchema.CUSTOM,
        timestamp=1.0,
    )
    f1 = KeypointFrame(
        points=[(0.0, 0.0)],
        confidences=[1.0],
        schema=KeypointSchema.CUSTOM,
        timestamp=0.0,
    )
    with pytest.raises(ValidationError):
        KeypointSequence(frames=[f0, f1], calibration=cal)


def test_keypoint_sequence_rejects_schema_mismatch() -> None:
    cal = make_calibration()
    f0 = KeypointFrame(
        points=[(0.0, 0.0)],
        confidences=[1.0],
        schema=KeypointSchema.CUSTOM,
        timestamp=0.0,
    )
    f1 = KeypointFrame(
        points=[(0.0, 0.0)],
        confidences=[1.0],
        schema=KeypointSchema.COCO_17,
        timestamp=1.0,
    )
    with pytest.raises(ValidationError):
        KeypointSequence(frames=[f0, f1], calibration=cal)


def test_keypoint_sequence_rejects_inconsistent_point_count() -> None:
    cal = make_calibration()
    f0 = KeypointFrame(
        points=[(0.0, 0.0)],
        confidences=[1.0],
        schema=KeypointSchema.CUSTOM,
        timestamp=0.0,
    )
    f1 = KeypointFrame(
        points=[(0.0, 0.0), (1.0, 1.0)],
        confidences=[1.0, 1.0],
        schema=KeypointSchema.CUSTOM,
        timestamp=1.0,
    )
    with pytest.raises(ValidationError):
        KeypointSequence(frames=[f0, f1], calibration=cal)


# ---------------------------------------------------------------------------
# MarkerSample / MarkerFrame / MarkerTrajectory
# ---------------------------------------------------------------------------


def test_marker_sample_valid() -> None:
    s = MarkerSample(xyz=(0.0, 1.0, 2.0))
    assert s.occluded is False


def test_marker_sample_occluded_allows_nan() -> None:
    s = MarkerSample(xyz=(math.nan, math.nan, math.nan), occluded=True)
    assert s.occluded


def test_marker_sample_rejects_non_finite_when_visible() -> None:
    with pytest.raises(ValidationError):
        MarkerSample(xyz=(math.nan, 0.0, 0.0), occluded=False)


def test_marker_frame_rejects_empty_samples() -> None:
    with pytest.raises(ValidationError):
        MarkerFrame(samples={}, timestamp=0.0)


def test_marker_trajectory_valid() -> None:
    t = make_marker_trajectory()
    assert len(t.frames) == 10


def test_marker_trajectory_rejects_inconsistent_label_set() -> None:
    f0 = MarkerFrame(samples={"A": MarkerSample(xyz=(0, 0, 0))}, timestamp=0.0)
    f1 = MarkerFrame(samples={"B": MarkerSample(xyz=(0, 0, 0))}, timestamp=1.0)
    with pytest.raises(ValidationError):
        MarkerTrajectory(frames=[f0, f1], unit_system=UnitSystem.METERS)


def test_marker_trajectory_rejects_non_monotonic_timestamps() -> None:
    f0 = MarkerFrame(samples={"A": MarkerSample(xyz=(0, 0, 0))}, timestamp=1.0)
    f1 = MarkerFrame(samples={"A": MarkerSample(xyz=(0, 0, 0))}, timestamp=0.0)
    with pytest.raises(ValidationError):
        MarkerTrajectory(frames=[f0, f1], unit_system=UnitSystem.METERS)


# ---------------------------------------------------------------------------
# JointAxis / JointLimit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("axis", ["X", "Y", "Z"])
def test_joint_axis_from_cardinal(axis: str) -> None:
    a = JointAxis.from_cardinal(axis)  # type: ignore[arg-type]
    assert math.isclose(sum(c * c for c in a.vector), 1.0)


def test_joint_axis_from_cardinal_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        JointAxis.from_cardinal("W")  # type: ignore[arg-type]


def test_joint_axis_rejects_non_unit_vector() -> None:
    with pytest.raises(ValidationError):
        JointAxis(vector=(2.0, 0.0, 0.0))


def test_joint_axis_rejects_zero_vector() -> None:
    with pytest.raises(ValidationError):
        JointAxis(vector=(0.0, 0.0, 0.0))


def test_joint_axis_rejects_non_finite() -> None:
    with pytest.raises(ValidationError):
        JointAxis(vector=(math.nan, 0.0, 0.0))


def test_joint_limit_valid() -> None:
    lim = JointLimit(lo=-1.0, hi=1.0)
    assert lim.lo < lim.hi


def test_joint_limit_lo_equal_hi_allowed() -> None:
    lim = JointLimit(lo=0.0, hi=0.0)
    assert lim.lo == lim.hi


def test_joint_limit_rejects_lo_gt_hi() -> None:
    with pytest.raises(ValidationError):
        JointLimit(lo=2.0, hi=1.0)


def test_joint_limit_rejects_non_finite() -> None:
    with pytest.raises(ValidationError):
        JointLimit(lo=math.nan, hi=1.0)


# ---------------------------------------------------------------------------
# SkeletonRig
# ---------------------------------------------------------------------------


def test_skeleton_rig_valid() -> None:
    rig = make_skeleton_rig(n_joints=4)
    assert rig.n_joints == 4


def test_skeleton_rig_rejects_duplicate_joint_names() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a", "a"],
            parents=[-1, 0],
            tpose_offsets=[(0, 0, 0), (0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z"), JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1), JointLimit(lo=-1, hi=1)],
        )


def test_skeleton_rig_rejects_empty_joint_name() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=[""],
            parents=[-1],
            tpose_offsets=[(0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1)],
        )


def test_skeleton_rig_rejects_length_mismatch() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a", "b"],
            parents=[-1],
            tpose_offsets=[(0, 0, 0), (0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z"), JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1), JointLimit(lo=-1, hi=1)],
        )


def test_skeleton_rig_rejects_self_parent() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a"],
            parents=[0],
            tpose_offsets=[(0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1)],
        )


def test_skeleton_rig_rejects_out_of_range_parent() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a", "b"],
            parents=[-1, 5],
            tpose_offsets=[(0, 0, 0), (0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z"), JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1), JointLimit(lo=-1, hi=1)],
        )


def test_skeleton_rig_rejects_cycle() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a", "b", "c"],
            parents=[1, 2, 0],  # cycle a->b->c->a
            tpose_offsets=[(0, 0, 0)] * 3,
            axes=[JointAxis.from_cardinal("Z")] * 3,
            limits=[JointLimit(lo=-1, hi=1)] * 3,
        )


def test_skeleton_rig_rejects_non_finite_offset() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a"],
            parents=[-1],
            tpose_offsets=[(math.nan, 0, 0)],
            axes=[JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1)],
        )


def test_skeleton_rig_rejects_unknown_semantic_label() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a"],
            parents=[-1],
            tpose_offsets=[(0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1)],
            semantic_labels={"root": "missing"},
        )


def test_skeleton_rig_rejects_unknown_end_effector() -> None:
    with pytest.raises(ValidationError):
        SkeletonRig(
            joint_names=["a"],
            parents=[-1],
            tpose_offsets=[(0, 0, 0)],
            axes=[JointAxis.from_cardinal("Z")],
            limits=[JointLimit(lo=-1, hi=1)],
            end_effectors=["missing"],
        )


# ---------------------------------------------------------------------------
# JointStateFrame / JointTrajectory
# ---------------------------------------------------------------------------


def test_joint_state_frame_optional_derivs() -> None:
    f = JointStateFrame(q=[0.0, 0.0], timestamp=0.0)
    assert f.qdot is None and f.qddot is None


def test_joint_state_frame_rejects_qdot_length_mismatch() -> None:
    with pytest.raises(ValidationError):
        JointStateFrame(q=[0.0, 0.0], qdot=[0.0], timestamp=0.0)


def test_joint_state_frame_rejects_qddot_length_mismatch() -> None:
    with pytest.raises(ValidationError):
        JointStateFrame(q=[0.0, 0.0], qddot=[0.0], timestamp=0.0)


def test_joint_state_frame_rejects_non_finite() -> None:
    with pytest.raises(ValidationError):
        JointStateFrame(q=[math.nan], timestamp=0.0)
    with pytest.raises(ValidationError):
        JointStateFrame(q=[0.0], qdot=[math.inf], timestamp=0.0)
    with pytest.raises(ValidationError):
        JointStateFrame(q=[0.0], qddot=[math.inf], timestamp=0.0)


def test_joint_state_frame_rejects_empty_q() -> None:
    with pytest.raises(ValidationError):
        JointStateFrame(q=[], timestamp=0.0)


def test_joint_trajectory_valid() -> None:
    rig = make_skeleton_rig(n_joints=3)
    jt = make_joint_trajectory(rig, n_frames=5)
    assert len(jt.frames) == 5


def test_joint_trajectory_rejects_dof_mismatch() -> None:
    rig = make_skeleton_rig(n_joints=3)
    bad_frame = JointStateFrame(q=[0.0, 0.0], timestamp=0.0)
    with pytest.raises(ValidationError):
        JointTrajectory(frames=[bad_frame], rig=rig)


def test_joint_trajectory_rejects_non_monotonic() -> None:
    rig = make_skeleton_rig(n_joints=2)
    f0 = JointStateFrame(q=[0.0, 0.0], timestamp=1.0)
    f1 = JointStateFrame(q=[0.0, 0.0], timestamp=0.0)
    with pytest.raises(ValidationError):
        JointTrajectory(frames=[f0, f1], rig=rig)


# ---------------------------------------------------------------------------
# MotionTrajectory
# ---------------------------------------------------------------------------


def test_motion_trajectory_valid() -> None:
    mt = make_motion_trajectory()
    assert mt.markers is not None
    assert mt.rig.n_joints == 6


def test_motion_trajectory_rejects_rig_mismatch() -> None:
    rig_a = make_skeleton_rig(n_joints=3)
    rig_b = make_skeleton_rig(n_joints=4)
    jt = make_joint_trajectory(rig_b, n_frames=2)
    prov = make_provenance()
    with pytest.raises(ValidationError):
        MotionTrajectory(rig=rig_a, joint_trajectory=jt, provenance=prov)


# ---------------------------------------------------------------------------
# CostWeights
# ---------------------------------------------------------------------------


def test_cost_weights_default_empty() -> None:
    cw = CostWeights()
    assert cw.weights == {}


def test_cost_weights_valid() -> None:
    cw = CostWeights(weights={"track": 1.5, "smooth": 0.0})
    assert cw.weights["track"] == 1.5


def test_cost_weights_rejects_negative() -> None:
    with pytest.raises(ValidationError):
        CostWeights(weights={"x": -0.1})


def test_cost_weights_rejects_non_finite() -> None:
    with pytest.raises(ValidationError):
        CostWeights(weights={"x": math.inf})


# ---------------------------------------------------------------------------
# MotionMatchingRequest
# ---------------------------------------------------------------------------


def test_motion_matching_request_valid() -> None:
    req = MotionMatchingRequest(
        reference=make_motion_trajectory(),
        cost_weights=CostWeights(weights={"track": 1.0}),
        time_horizon=1.5,
        engine=EngineType.MUJOCO,
    )
    assert req.engine == EngineType.MUJOCO


def test_motion_matching_request_optional_horizon() -> None:
    req = MotionMatchingRequest(
        reference=make_motion_trajectory(),
        cost_weights=CostWeights(),
        engine=EngineType.DRAKE,
    )
    assert req.time_horizon is None


@pytest.mark.parametrize("bad", [0.0, -1.0, math.inf, math.nan])
def test_motion_matching_request_rejects_bad_horizon(bad: float) -> None:
    with pytest.raises(ValidationError):
        MotionMatchingRequest(
            reference=make_motion_trajectory(),
            cost_weights=CostWeights(),
            time_horizon=bad,
            engine=EngineType.PINOCCHIO,
        )


# ---------------------------------------------------------------------------
# TorqueTrajectory / MuscleActivationTrajectory
# ---------------------------------------------------------------------------


def test_torque_trajectory_valid() -> None:
    tt = TorqueTrajectory(
        frames=[(0.0, [0.0, 0.0]), (0.1, [1.0, -1.0])],
        rig_joint_names=["a", "b"],
    )
    assert len(tt.frames) == 2


def test_torque_trajectory_rejects_dim_mismatch() -> None:
    with pytest.raises(ValidationError):
        TorqueTrajectory(
            frames=[(0.0, [0.0])],
            rig_joint_names=["a", "b"],
        )


def test_torque_trajectory_rejects_non_monotonic() -> None:
    with pytest.raises(ValidationError):
        TorqueTrajectory(
            frames=[(1.0, [0.0]), (0.0, [0.0])],
            rig_joint_names=["a"],
        )


def test_torque_trajectory_rejects_non_finite() -> None:
    with pytest.raises(ValidationError):
        TorqueTrajectory(
            frames=[(0.0, [math.inf])],
            rig_joint_names=["a"],
        )


def test_muscle_activation_valid() -> None:
    m = MuscleActivationTrajectory(
        frames=[(0.0, [0.0, 1.0]), (0.1, [0.5, 0.5])],
        muscle_names=["m1", "m2"],
    )
    assert m.muscle_names[0] == "m1"


def test_muscle_activation_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        MuscleActivationTrajectory(
            frames=[(0.0, [1.5])],
            muscle_names=["m1"],
        )


def test_muscle_activation_rejects_duplicate_names() -> None:
    with pytest.raises(ValidationError):
        MuscleActivationTrajectory(
            frames=[(0.0, [0.0, 0.0])],
            muscle_names=["m1", "m1"],
        )


def test_muscle_activation_rejects_dim_mismatch() -> None:
    with pytest.raises(ValidationError):
        MuscleActivationTrajectory(
            frames=[(0.0, [0.0])],
            muscle_names=["m1", "m2"],
        )


def test_muscle_activation_rejects_non_monotonic() -> None:
    with pytest.raises(ValidationError):
        MuscleActivationTrajectory(
            frames=[(1.0, [0.0]), (0.0, [0.0])],
            muscle_names=["m1"],
        )


# ---------------------------------------------------------------------------
# ResidualReport / MotionMatchingResult
# ---------------------------------------------------------------------------


def test_residual_report_valid() -> None:
    r = ResidualReport(
        per_joint_rmse={"a": 0.1, "b": 0.2},
        aggregate_rmse=0.15,
        notes="ok",
    )
    assert r.aggregate_rmse == 0.15


def test_residual_report_rejects_negative_per_joint() -> None:
    with pytest.raises(ValidationError):
        ResidualReport(per_joint_rmse={"a": -1.0}, aggregate_rmse=0.0)


def test_residual_report_rejects_non_finite_aggregate() -> None:
    with pytest.raises(ValidationError):
        ResidualReport(per_joint_rmse={}, aggregate_rmse=math.nan)


def test_residual_report_rejects_negative_aggregate() -> None:
    with pytest.raises(ValidationError):
        ResidualReport(per_joint_rmse={}, aggregate_rmse=-1.0)


def test_motion_matching_result_requires_at_least_one_control() -> None:
    rig = make_skeleton_rig(n_joints=2)
    jt = make_joint_trajectory(rig, n_frames=2)
    with pytest.raises(ValidationError):
        MotionMatchingResult(
            tracked=jt,
            torques=None,
            activations=None,
            residuals=ResidualReport(per_joint_rmse={}, aggregate_rmse=0.0),
            provenance=make_provenance(),
        )


def test_motion_matching_result_with_torques() -> None:
    rig = make_skeleton_rig(n_joints=2)
    jt = make_joint_trajectory(rig, n_frames=2)
    tt = TorqueTrajectory(
        frames=[(0.0, [0.0, 0.0])],
        rig_joint_names=rig.joint_names,
    )
    res = MotionMatchingResult(
        tracked=jt,
        torques=tt,
        residuals=ResidualReport(per_joint_rmse={}, aggregate_rmse=0.0),
        provenance=make_provenance(),
    )
    assert res.torques is not None and res.activations is None


def test_motion_matching_result_with_activations() -> None:
    rig = make_skeleton_rig(n_joints=2)
    jt = make_joint_trajectory(rig, n_frames=2)
    act = MuscleActivationTrajectory(
        frames=[(0.0, [0.5])],
        muscle_names=["biceps"],
    )
    res = MotionMatchingResult(
        tracked=jt,
        activations=act,
        residuals=ResidualReport(per_joint_rmse={}, aggregate_rmse=0.0),
        provenance=make_provenance(),
    )
    assert res.activations is not None


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_provenance_default_factory_created_at() -> None:
    p = Provenance(software_version="0.1.0")
    assert p.created_at is not None
    assert p.sport == "golf"


# ---------------------------------------------------------------------------
# JSON round-trips
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "obj",
    [
        make_calibration(),
        make_keypoint_sequence(n_frames=3, n_points=4, schema=KeypointSchema.CUSTOM),
        make_marker_trajectory(n_frames=3),
        make_skeleton_rig(n_joints=4),
        make_motion_trajectory(),
        CostWeights(weights={"a": 1.0, "b": 0.0}),
        ResidualReport(per_joint_rmse={"a": 0.1}, aggregate_rmse=0.1),
        Provenance(software_version="1.2.3"),
        TorqueTrajectory(frames=[(0.0, [0.0])], rig_joint_names=["x"]),
        MuscleActivationTrajectory(frames=[(0.0, [0.0])], muscle_names=["m1"]),
    ],
)
def test_json_round_trip(obj: object) -> None:
    cls = type(obj)
    raw = obj.model_dump_json()  # type: ignore[attr-defined]
    restored = cls.model_validate_json(raw)  # type: ignore[attr-defined]
    assert restored == obj


def test_motion_matching_request_round_trip() -> None:
    req = MotionMatchingRequest(
        reference=make_motion_trajectory(),
        cost_weights=CostWeights(weights={"track": 1.0}),
        time_horizon=1.0,
        engine=EngineType.MUJOCO,
    )
    raw = req.model_dump_json()
    assert MotionMatchingRequest.model_validate_json(raw) == req


def test_motion_matching_result_round_trip() -> None:
    rig = make_skeleton_rig(n_joints=2)
    jt = make_joint_trajectory(rig, n_frames=2)
    tt = TorqueTrajectory(frames=[(0.0, [0.0, 0.0])], rig_joint_names=rig.joint_names)
    res = MotionMatchingResult(
        tracked=jt,
        torques=tt,
        residuals=ResidualReport(per_joint_rmse={}, aggregate_rmse=0.0),
        provenance=make_provenance(),
    )
    raw = res.model_dump_json()
    assert MotionMatchingResult.model_validate_json(raw) == res
