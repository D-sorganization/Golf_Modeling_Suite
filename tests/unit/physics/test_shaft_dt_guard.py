"""Tests for dt <= 0 guard in FiniteElementShaftModel.step().

Covers issue #3054: integrator must raise ValueError for non-positive dt
to prevent silent division-by-zero in the Newmark-beta formulation.
"""

from __future__ import annotations

import pytest

from src.shared.python.physics.flexible_shaft import (
    FiniteElementShaftModel,
    ShaftMaterial,
    ShaftProperties,
)


@pytest.fixture()
def initialized_fem() -> FiniteElementShaftModel:
    """Return a fully initialized FE shaft model ready to step."""
    import numpy as np

    model = FiniteElementShaftModel(n_elements=4)
    # Create minimal shaft properties
    props = ShaftProperties(
        length=1.0,
        outer_diameter=np.array([0.01, 0.01, 0.01, 0.01, 0.01]),
        wall_thickness=np.array([0.001, 0.001, 0.001, 0.001, 0.001]),
        station_positions=np.array([0.0, 0.25, 0.5, 0.75, 1.0]),
        material=ShaftMaterial.STEEL,
    )
    model.initialize(props)
    return model


class TestStepDtGuard:
    """Verify that step() rejects non-positive dt values."""

    def test_step_dt_zero_raises(
        self, initialized_fem: FiniteElementShaftModel
    ) -> None:
        """step(dt=0) must raise ValueError."""
        with pytest.raises(ValueError, match="dt must be positive"):
            initialized_fem.step(dt=0)

    def test_step_dt_negative_raises(
        self, initialized_fem: FiniteElementShaftModel
    ) -> None:
        """step(dt=-1) must raise ValueError."""
        with pytest.raises(ValueError, match="dt must be positive"):
            initialized_fem.step(dt=-1)

    def test_step_dt_negative_float_raises(
        self, initialized_fem: FiniteElementShaftModel
    ) -> None:
        """step(dt=-1e-6) must raise ValueError (small negative)."""
        with pytest.raises(ValueError, match="dt must be positive"):
            initialized_fem.step(dt=-1e-6)

    def test_step_dt_positive_succeeds(
        self, initialized_fem: FiniteElementShaftModel
    ) -> None:
        """step(dt=0.001) must succeed and return a ShaftState."""
        state = initialized_fem.step(dt=0.001)
        assert state is not None
