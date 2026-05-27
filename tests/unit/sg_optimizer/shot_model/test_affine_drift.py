"""Tests for AffineDrift integration."""

from __future__ import annotations

import pytest

from src.shared.python.contracts import ContractViolationError
from src.shared.python.sg_optimizer.shot_model.affine_drift import (
    derive_dispersion_from_simulation,
)


def test_derive_dispersion_scales_with_variance():
    sim_output = {
        "drift_variance": 4.0,
        "control_variance": 9.0,
    }
    dist = derive_dispersion_from_simulation(
        sim_output,
        base_sigma_long=10.0,
        base_sigma_lat=5.0,
        base_rho=0.2,
    )
    assert dist.sigma_long == pytest.approx(20.0)  # 10.0 * sqrt(4.0)
    assert dist.sigma_lat == pytest.approx(15.0)  # 5.0 * sqrt(9.0)
    assert dist.rho == 0.2


def test_derive_dispersion_missing_keys():
    with pytest.raises(ContractViolationError, match="must contain 'drift_variance'"):
        derive_dispersion_from_simulation({"control_variance": 1.0}, 10.0, 5.0)

    with pytest.raises(ContractViolationError, match="must contain 'control_variance'"):
        derive_dispersion_from_simulation({"drift_variance": 1.0}, 10.0, 5.0)


def test_derive_dispersion_negative_variance():
    with pytest.raises(ContractViolationError, match="must be non-negative"):
        derive_dispersion_from_simulation(
            {"drift_variance": -1.0, "control_variance": 1.0}, 10.0, 5.0
        )
