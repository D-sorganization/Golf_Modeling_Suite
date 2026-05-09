"""Tests for model-family polynomial theta contracts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.shared.python.motion_matching.polynomial_contracts import (
    COEFFICIENT_LETTERS,
    FULLBODY_LEG_FAMILIES,
    polynomial_contract,
    validate_theta_for_model_family,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "simscape_polynomial_contracts.json"
)


@pytest.mark.unit
def test_legacy_3d_golf_contract_remains_189_coefficients() -> None:
    contract = polynomial_contract("3d_golf")

    assert len(contract.joint_families) == 27
    assert contract.theta_size == 189
    assert contract.coefficient_names[:7] == tuple(
        f"HipInputX{letter}" for letter in COEFFICIENT_LETTERS
    )


@pytest.mark.unit
def test_fullbody_contract_counts_axes_and_resolves_33_vs_39_ambiguity() -> None:
    contract = polynomial_contract("3d_fullbody")

    assert len(FULLBODY_LEG_FAMILIES) == 12
    assert len(contract.joint_families) == 39
    assert contract.theta_size == 273

    for family in FULLBODY_LEG_FAMILIES:
        for letter in COEFFICIENT_LETTERS:
            assert f"{family}{letter}" in contract.coefficient_names


@pytest.mark.unit
def test_contract_fixture_matches_python_contract() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["coefficient_letters"] == list(COEFFICIENT_LETTERS)
    assert (
        fixture["model_families"]["3d_golf"]["theta_size"]
        == polynomial_contract("3d_golf").theta_size
    )
    assert (
        fixture["model_families"]["3d_fullbody"]["theta_size"]
        == polynomial_contract("3d_fullbody").theta_size
    )
    assert (
        tuple(fixture["model_families"]["3d_fullbody"]["leg_families"])
        == FULLBODY_LEG_FAMILIES
    )


@pytest.mark.unit
def test_validate_theta_for_model_family_rejects_wrong_family_length() -> None:
    fullbody_theta = np.zeros(polynomial_contract("3d_fullbody").theta_size)
    legacy_theta = np.zeros(polynomial_contract("3d_golf").theta_size)

    np.testing.assert_array_equal(
        validate_theta_for_model_family(fullbody_theta, model_family="3d_fullbody"),
        fullbody_theta,
    )

    with pytest.raises(ValueError, match="39\\*7 = 273"):
        validate_theta_for_model_family(legacy_theta, model_family="3d_fullbody")
