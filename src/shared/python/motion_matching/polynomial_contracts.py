"""Model-family polynomial coefficient contracts for Simscape motion matching.

The legacy ``3D_Golf_Model`` discovers 27 seven-coefficient joint families from
``PolynomialInputValues.mat``. The full-body derivative adds hip, knee, and
ankle axis families for both legs. Because the MATLAB discovery helper counts
each actuated axis as its own family, the full-body contract is 39 families, not
33 aggregate anatomical joints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
from numpy.typing import NDArray

from src.shared.python.motion_matching.validate_theta import validate_theta

ModelFamily = Literal["3d_golf", "3d_fullbody"]

COEFFICIENT_LETTERS: Final[tuple[str, ...]] = ("A", "B", "C", "D", "E", "F", "G")
COEFFICIENTS_PER_FAMILY: Final[int] = len(COEFFICIENT_LETTERS)

LEGACY_3D_GOLF_FAMILIES: Final[tuple[str, ...]] = (
    "HipInputX",
    "HipInputY",
    "HipInputZ",
    "LEInput",
    "LFInput",
    "LSInputX",
    "LSInputY",
    "LSInputZ",
    "LScapInputX",
    "LScapInputY",
    "LWInputX",
    "LWInputY",
    "REInput",
    "RFInput",
    "RSInputX",
    "RSInputY",
    "RSInputZ",
    "RScapInputX",
    "RScapInputY",
    "RWInputX",
    "RWInputY",
    "SpineInputX",
    "SpineInputY",
    "TorsoInput",
    "TranslationInputX",
    "TranslationInputY",
    "TranslationInputZ",
)

FULLBODY_LEG_FAMILIES: Final[tuple[str, ...]] = (
    "LAnkleX",
    "LAnkleY",
    "LHipX",
    "LHipY",
    "LHipZ",
    "LKnee",
    "RAnkleX",
    "RAnkleY",
    "RHipX",
    "RHipY",
    "RHipZ",
    "RKnee",
)

FULLBODY_3D_FAMILIES: Final[tuple[str, ...]] = tuple(
    sorted((*LEGACY_3D_GOLF_FAMILIES, *FULLBODY_LEG_FAMILIES))
)


@dataclass(frozen=True)
class PolynomialContract:
    """Resolved polynomial coefficient layout for a Simscape model family."""

    model_family: ModelFamily
    joint_families: tuple[str, ...]
    coefficient_letters: tuple[str, ...] = COEFFICIENT_LETTERS

    @property
    def theta_size(self) -> int:
        """Flat theta length for this model family."""
        return len(self.joint_families) * len(self.coefficient_letters)

    @property
    def coefficient_names(self) -> tuple[str, ...]:
        """Flattened ``<Family><A..G>`` coefficient names in contract order."""
        return tuple(
            f"{family}{letter}"
            for family in self.joint_families
            for letter in self.coefficient_letters
        )


def polynomial_contract(model_family: ModelFamily) -> PolynomialContract:
    """Return the explicit polynomial contract for a supported model family."""
    if model_family == "3d_golf":
        return PolynomialContract(model_family, LEGACY_3D_GOLF_FAMILIES)
    if model_family == "3d_fullbody":
        return PolynomialContract(model_family, FULLBODY_3D_FAMILIES)
    raise ValueError(f"Unsupported model family: {model_family!r}")


def validate_theta_for_model_family(
    theta: object,
    *,
    model_family: ModelFamily,
    name: str = "theta",
) -> NDArray[np.float64]:
    """Validate theta against the model-family-specific coefficient contract."""
    contract = polynomial_contract(model_family)
    return validate_theta(theta, n_joints=len(contract.joint_families), name=name)


__all__ = [
    "COEFFICIENT_LETTERS",
    "COEFFICIENTS_PER_FAMILY",
    "FULLBODY_3D_FAMILIES",
    "FULLBODY_LEG_FAMILIES",
    "LEGACY_3D_GOLF_FAMILIES",
    "ModelFamily",
    "PolynomialContract",
    "polynomial_contract",
    "validate_theta_for_model_family",
]
