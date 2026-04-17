"""Contracts for humanoid URDF assets used in golf biomechanics."""

from __future__ import annotations

from pathlib import Path

from src.shared.python.biomechanics.humanoid_urdf_contracts import (
    biomechanical_humanoid_models,
    load_model_metadata,
    parse_urdf_summary,
    validate_bilateral_grip_constraints,
    validate_major_joint_coverage,
)
from src.shared.python.config.standard_models import StandardModelManager

REPO_ROOT = Path(__file__).parents[2]
SIMPLE_HUMANOID_URDF = REPO_ROOT / "src/shared/urdf/simple_humanoid.urdf"
STANDARD_MODELS_YAML = REPO_ROOT / "src/shared/urdf/standard_models.yaml"
GOLFER_URDF = (
    REPO_ROOT / "src/engines/physics_engines/pinocchio/models/generated/golfer.urdf"
)
GOLFER_SPEC = (
    REPO_ROOT
    / "src/engines/physics_engines/pinocchio/models/spec/golfer_canonical.yaml"
)


def test_simple_humanoid_is_smoke_only_in_standard_model_metadata() -> None:
    """The toy humanoid must not be discoverable as biomechanics-ready."""
    metadata = load_model_metadata(STANDARD_MODELS_YAML)

    simple = metadata["simple_humanoid"]
    assert simple["validation_scope"] == "smoke_test"
    assert simple["biomechanics_ready"] is False
    assert "simple_humanoid" not in biomechanical_humanoid_models(metadata)


def test_standard_model_manager_excludes_smoke_humanoid_from_biomechanics() -> None:
    """Biomechanics discovery excludes parser smoke fixtures."""
    manager = StandardModelManager(REPO_ROOT / "src")

    biomechanical_models = manager.list_biomechanical_humanoid_models()

    assert "standard" in biomechanical_models
    assert "simple" not in biomechanical_models


def test_simple_humanoid_fails_major_joint_contract() -> None:
    """The legacy simple model is intentionally too small for swing biomechanics."""
    summary = parse_urdf_summary(SIMPLE_HUMANOID_URDF)

    issues = validate_major_joint_coverage(summary)

    assert issues
    assert any(issue.requirement == "left elbow" for issue in issues)
    assert any(issue.requirement == "movable joint count" for issue in issues)


def test_generated_golfer_satisfies_major_joint_contract() -> None:
    """The generated golfer asset must retain major limb and grip DOFs."""
    summary = parse_urdf_summary(GOLFER_URDF)

    issues = validate_major_joint_coverage(summary)

    assert issues == ()


def test_canonical_golfer_spec_declares_bilateral_grip_constraints() -> None:
    """Right and left hands must both have explicit club grip constraints."""
    missing = validate_bilateral_grip_constraints(GOLFER_SPEC)

    assert missing == ()
