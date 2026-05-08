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
VALIDATE_3D_FULLBODY = (
    REPO_ROOT
    / "src"
    / "engines"
    / "Simscape_Multibody_Models"
    / "3D_FullBody_Model"
    / "matlab"
    / "scripts"
    / "validate_3d_fullbody.m"
)


def test_leg_chain_declares_mirrored_anchor_blocks() -> None:
    """The mirrored implementation must name both leg anchor sets."""
    text = ADD_LEG_CHAIN.read_text(encoding="utf-8")

    required_names = {
        "%s Leg Kinetically Driven",
        "Pelvis_Frame",
        "JointTorque%sHipX",
        "JointTorque%sHipY",
        "JointTorque%sHipZ",
        "JointTorque%sKnee",
        "JointTorque%sAnkleX",
        "JointTorque%sAnkleY",
        "%sHip_Gimbal",
        "%sUpperLeg_CylindricalSolid",
        "%sKnee_Revolute",
        "%sLowerLeg_CylindricalSolid",
        "%sAnkle_Universal",
        "%sFoot_BrickSolid",
        "%sBallOfFoot_Sphere",
        "%sFoot_Frame",
    }

    missing = sorted(name for name in required_names if name not in text)
    assert not missing


def test_mirrored_leg_chain_is_idempotent_and_reports_partial_builds() -> None:
    """Reruns must delete/rebuild and preserve a validation report."""
    text = ADD_LEG_CHAIN.read_text(encoding="utf-8")

    assert "delete_block(subsystem_path)" in text
    assert "local_build_leg(char(opts.leg_root_path), opts, 'L', 'Left'" in text
    assert "local_build_leg(char(opts.leg_root_path), opts, 'R', 'Right'" in text
    assert "local_try_add_block" in text
    assert "local_try_add_line" in text
    assert "operation_log" in text
    assert "partial_with_reported_failures" in text


def test_ground_contact_contract_declares_required_blocks_and_parameters() -> None:
    """The second-leg slice must expose a configurable contact contract."""
    text = ADD_LEG_CHAIN.read_text(encoding="utf-8")

    required_names = {
        "Ground Contact Forces",
        "Ground_Plane_Z0",
        "LFoot_Ground_Contact_Force",
        "RFoot_Ground_Contact_Force",
        "LGroundReactionForce",
        "RGroundReactionForce",
        "GroundContactStiffness",
        "GroundContactDamping",
        "GroundFrictionStatic",
        "GroundFrictionKinetic",
    }

    missing = sorted(name for name in required_names if name not in text)
    assert not missing


def test_validation_report_includes_contact_contract() -> None:
    """Validation must report both-leg/contact block presence explicitly."""
    text = VALIDATE_3D_FULLBODY.read_text(encoding="utf-8")

    required_names = {
        "contact_contract",
        "local_contact_contract_report",
        "Left Leg Kinetically Driven",
        "Right Leg Kinetically Driven",
        "Ground Contact Forces",
        "LFoot_Ground_Contact_Force",
        "RFoot_Ground_Contact_Force",
        "static_pose_check",
    }

    missing = sorted(name for name in required_names if name not in text)
    assert not missing
