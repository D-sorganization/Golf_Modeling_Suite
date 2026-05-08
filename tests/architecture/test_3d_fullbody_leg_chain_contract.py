"""Contract tests for the scripted 3D full-body leg-chain slice."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ADD_LEG_CHAIN = (
    REPO_ROOT
    / "src"
    / "engines"
    / "Simscape_Multibody_Models"
    / "3D_FullBody_Model"
    / "matlab"
    / "scripts"
    / "add_leg_chain.m"
)


def test_left_leg_chain_declares_required_anchor_blocks() -> None:
    """The first implementation slice must name all left-leg anchors."""
    text = ADD_LEG_CHAIN.read_text(encoding="utf-8")

    required_names = {
        "Left Leg Kinetically Driven",
        "Pelvis_Frame",
        "JointTorqueLHipX",
        "JointTorqueLHipY",
        "JointTorqueLHipZ",
        "JointTorqueLKnee",
        "JointTorqueLAnkleX",
        "JointTorqueLAnkleY",
        "LHip_Gimbal",
        "LUpperLeg_CylindricalSolid",
        "LKnee_Revolute",
        "LLowerLeg_CylindricalSolid",
        "LAnkle_Universal",
        "LFoot_BrickSolid",
        "LBallOfFoot_Sphere",
        "LFoot_Frame",
    }

    missing = sorted(name for name in required_names if name not in text)
    assert not missing


def test_left_leg_chain_is_idempotent_and_reports_partial_builds() -> None:
    """Reruns must delete/rebuild and preserve a validation report."""
    text = ADD_LEG_CHAIN.read_text(encoding="utf-8")

    assert "delete_block(subsystem_path)" in text
    assert "local_try_add_block" in text
    assert "local_try_add_line" in text
    assert "operation_log" in text
    assert "partial_with_reported_failures" in text
    assert "Right-side mirror is intentionally left for the next issue slice" in text
