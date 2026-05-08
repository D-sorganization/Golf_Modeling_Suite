"""Tests for starting-pose matcher durable session schema."""

import pytest

from src.tools.starting_pose_matcher.session_schema import (
    REQUIRED_SKELETON_JOINTS,
    SESSION_SCHEMA_VERSION,
    SKELETON_VOCABULARY_VERSION,
    ProviderMetadata,
    SelectedFrame,
    SessionSchemaError,
    SessionTransform,
    StartingPoseSession,
    TargetSourceMetadata,
    session_from_dict,
    validate_provider_parity,
)


def test_session_round_trip_preserves_provider_metadata_and_transform():
    session = StartingPoseSession(
        version=SESSION_SCHEMA_VERSION,
        target_source=TargetSourceMetadata(
            source_type="xlsx",
            path="targets/session.xlsx",
            sheet="trial-01",
            metadata={"subject": "demo"},
        ),
        provider=ProviderMetadata(
            provider_id="mujoco",
            metadata={"model": "minimal_golfer"},
        ),
        model_path="models/golfer.xml",
        config_path="configs/session.toml",
        selected_frame=SelectedFrame(event="I", frame_index=123, phase="downswing"),
        skeleton_vocabulary_version=SKELETON_VOCABULARY_VERSION,
        transform=SessionTransform(
            tx=1.0,
            ty=2.0,
            tz=3.0,
            rx=4.0,
            ry=5.0,
            rz=6.0,
            scale=1.25,
        ),
        quality_metrics={"midpoint_rmse_mm": 7.5, "clubhead_rmse_mm": 8.5},
        simscape_mat_output_path="out/session.mat",
    )

    parsed = session_from_dict(session.to_dict())

    assert parsed == session
    assert parsed.provider.metadata == {"model": "minimal_golfer"}
    assert parsed.transform.rz == 6.0
    assert parsed.simscape_mat_output_path == "out/session.mat"


def test_unsupported_old_version_has_clear_error():
    payload = {
        "version": SESSION_SCHEMA_VERSION - 1,
        "target_source": {"source_type": "xlsx", "path": "target.xlsx"},
        "provider": {"provider_id": "simscape"},
        "model_path": "model.slx",
        "config_path": None,
        "selected_frame": {"event": "A", "frame_index": 0},
        "skeleton_vocabulary_version": SKELETON_VOCABULARY_VERSION,
        "transform": {},
        "quality_metrics": {},
    }

    with pytest.raises(SessionSchemaError, match="Unsupported.*schema version"):
        session_from_dict(payload)


def test_bad_provider_id_has_actionable_error():
    payload = {
        "version": SESSION_SCHEMA_VERSION,
        "target_source": {"source_type": "xlsx", "path": "target.xlsx"},
        "provider": {"provider_id": "unknown_engine"},
        "model_path": "model.xml",
        "config_path": None,
        "selected_frame": {"event": "A", "frame_index": 0},
        "skeleton_vocabulary_version": SKELETON_VOCABULARY_VERSION,
        "transform": {},
        "quality_metrics": {},
    }

    with pytest.raises(SessionSchemaError, match="Use one of:"):
        session_from_dict(payload)


def test_parity_matrix_accepts_fake_physics_providers():
    fake_skeleton = {joint: object() for joint in REQUIRED_SKELETON_JOINTS}

    rows = [
        validate_provider_parity(
            provider_id,
            fake_skeleton,
            units="m",
            coordinate_frame="matcher world",
            optional_dependency_behavior="typed unavailable error",
        )
        for provider_id in ("simscape", "mujoco", "drake", "pinocchio", "opensim")
    ]

    assert [row["provider_id"] for row in rows] == [
        "simscape",
        "mujoco",
        "drake",
        "pinocchio",
        "opensim",
    ]
    assert all(row["required_joints"] == list(REQUIRED_SKELETON_JOINTS) for row in rows)


def test_parity_matrix_accepts_observed_provider_subset_with_typed_errors():
    observed_skeleton = {
        joint: object()
        for joint in ("hip", "spine", "ls", "rs", "le", "re", "lw", "rw")
    }

    row = validate_provider_parity(
        "openpose",
        observed_skeleton,
        units="calibrated units",
        coordinate_frame="target frame",
        optional_dependency_behavior="typed parse/dependency errors",
    )

    assert row["provider_id"] == "openpose"
    assert "ch" not in row["required_joints"]


def test_parity_matrix_missing_required_joint_is_actionable():
    incomplete_skeleton = {joint: object() for joint in REQUIRED_SKELETON_JOINTS}
    incomplete_skeleton.pop("ch")

    with pytest.raises(
        SessionSchemaError, match="missing required skeleton joints: ch"
    ):
        validate_provider_parity(
            "mujoco",
            incomplete_skeleton,
            units="m",
            coordinate_frame="matcher world",
            optional_dependency_behavior="typed unavailable error",
        )
