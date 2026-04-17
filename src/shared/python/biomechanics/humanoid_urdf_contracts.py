"""Validation contracts for humanoid golf URDF assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
import yaml  # type: ignore[import-untyped]

MOVABLE_URDF_JOINT_TYPES = {"continuous", "prismatic", "revolute"}
BIOMECHANICAL_MODEL_SCOPES = {"biomechanical", "research"}
SMOKE_TEST_SCOPE = "smoke_test"


@dataclass(frozen=True)
class JointContractIssue:
    """A failed humanoid joint contract requirement."""

    requirement: str
    expected: str
    observed: int


@dataclass(frozen=True)
class UrdfJoint:
    """Minimal URDF joint metadata needed for model contract checks."""

    name: str
    joint_type: str
    parent: str
    child: str


@dataclass(frozen=True)
class HumanoidUrdfSummary:
    """Parsed URDF metadata used by biomechanical readiness checks."""

    links: frozenset[str]
    joints: tuple[UrdfJoint, ...]

    @property
    def movable_joints(self) -> tuple[UrdfJoint, ...]:
        """Return non-fixed joints that add kinematic DOFs."""
        return tuple(
            joint
            for joint in self.joints
            if joint.joint_type in MOVABLE_URDF_JOINT_TYPES
        )


def parse_urdf_summary(urdf_path: Path) -> HumanoidUrdfSummary:
    """Parse links and joints from a URDF file."""
    root = ET.parse(urdf_path).getroot()
    links = frozenset(
        str(link.attrib["name"])
        for link in root.findall("link")
        if "name" in link.attrib
    )
    joints: list[UrdfJoint] = []

    for joint in root.findall("joint"):
        parent = joint.find("parent")
        child = joint.find("child")
        if parent is None or child is None:
            continue
        joints.append(
            UrdfJoint(
                name=str(joint.attrib.get("name", "")),
                joint_type=str(joint.attrib.get("type", "")),
                parent=str(parent.attrib.get("link", "")),
                child=str(child.attrib.get("link", "")),
            )
        )

    return HumanoidUrdfSummary(links=links, joints=tuple(joints))


def validate_major_joint_coverage(
    summary: HumanoidUrdfSummary,
    *,
    minimum_movable_joints: int = 30,
) -> tuple[JointContractIssue, ...]:
    """Validate that a humanoid URDF has minimum golf-biomechanics joint coverage."""
    issues: list[JointContractIssue] = []
    movable_names = [joint.name for joint in summary.movable_joints]
    requirements = {
        "left shoulder": ("shoulder_left", "upper_arm_left"),
        "right shoulder": ("shoulder_right", "upper_arm_right"),
        "left elbow": ("forearm_left",),
        "right elbow": ("forearm_right",),
        "left wrist": ("hand_left",),
        "right wrist": ("hand_right",),
        "left fingers": ("fingers_left",),
        "right fingers": ("fingers_right",),
        "left hip": ("left_thigh", "thigh_left"),
        "right hip": ("right_thigh", "thigh_right"),
        "left knee": ("left_shank", "shank_left"),
        "right knee": ("right_shank", "shank_right"),
        "left ankle": ("left_foot", "foot_left"),
        "right ankle": ("right_foot", "foot_right"),
        "segmented spine": ("lumbar", "thorax"),
    }

    for label, tokens in requirements.items():
        observed = sum(
            1 for name in movable_names if any(token in name for token in tokens)
        )
        if observed == 0:
            issues.append(
                JointContractIssue(
                    requirement=label,
                    expected=f"at least one movable joint containing {tokens}",
                    observed=observed,
                )
            )

    if len(movable_names) < minimum_movable_joints:
        issues.append(
            JointContractIssue(
                requirement="movable joint count",
                expected=f"at least {minimum_movable_joints} movable joints",
                observed=len(movable_names),
            )
        )

    return tuple(issues)


def load_model_metadata(config_path: Path) -> dict[str, Any]:
    """Load the standard-model metadata YAML."""
    with config_path.open() as config_file:
        return yaml.safe_load(config_file) or {}


def biomechanical_humanoid_models(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return humanoid entries that are explicitly biomechanical/research scope."""
    return {
        key: value
        for key, value in config.items()
        if isinstance(value, dict)
        and str(value.get("model_family", "")).lower() == "humanoid"
        and str(value.get("validation_scope", "")).lower() in BIOMECHANICAL_MODEL_SCOPES
    }


def validate_bilateral_grip_constraints(spec_path: Path) -> tuple[str, ...]:
    """Validate that the canonical golfer spec declares both hand-to-club grips."""
    with spec_path.open() as spec_file:
        spec = yaml.safe_load(spec_file) or {}

    constraints = {
        str(constraint.get("name", "")): constraint
        for constraint in spec.get("constraints", [])
        if isinstance(constraint, dict)
    }
    missing: list[str] = []

    expected = {
        "right_hand_to_club": ("right_hand/", "club_shaft/"),
        "left_hand_to_club": ("left_hand/", "club_shaft/"),
    }
    for name, (hand_prefix, club_prefix) in expected.items():
        constraint = constraints.get(name)
        if constraint is None:
            missing.append(name)
            continue
        if constraint.get("type") != "rigid":
            missing.append(f"{name}:rigid")
        if not str(constraint.get("frameA", "")).startswith(hand_prefix):
            missing.append(f"{name}:frameA")
        if not str(constraint.get("frameB", "")).startswith(club_prefix):
            missing.append(f"{name}:frameB")

    return tuple(missing)
