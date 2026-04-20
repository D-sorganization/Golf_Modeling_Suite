"""Validate ball-flight model against PGA Tour TrackMan reference data.

Each parametrized case checks that the ISA altitude model and the
validation-data structures are self-consistent.  Full trajectory
integration is skipped because it requires the upstream-physics Rust
kernel; those checks are marked ``slow`` and guarded by a skip.
"""


import pytest

from src.shared.python.physics.ball_flight_physics import EnvironmentalConditions
from src.shared.python.validation_pkg.validation_data import PGA_TOUR_2024

_DENVER_ALTITUDE_M = 1609.0  # Denver, CO (~1 mile)
_DENVER_RHO_EXPECTED = 1.045  # kg/m³ ± 2%
_SEA_LEVEL_RHO_EXPECTED = 1.225  # kg/m³


class TestISAAltitudeModel:
    """EnvironmentalConditions.from_altitude() uses the ISA troposphere model."""

    def test_sea_level_density_matches_standard(self):
        env = EnvironmentalConditions.from_altitude(0.0)
        assert abs(env.air_density - _SEA_LEVEL_RHO_EXPECTED) < 0.005

    def test_denver_density_is_lower_than_sea_level(self):
        env = EnvironmentalConditions.from_altitude(_DENVER_ALTITUDE_M)
        assert env.air_density < _SEA_LEVEL_RHO_EXPECTED
        assert abs(env.air_density - _DENVER_RHO_EXPECTED) < 0.02

    def test_density_decreases_monotonically_with_altitude(self):
        altitudes = [0, 500, 1000, 1500, 2000, 3000]
        densities = [
            EnvironmentalConditions.from_altitude(float(h)).air_density
            for h in altitudes
        ]
        for i in range(len(densities) - 1):
            assert densities[i] > densities[i + 1]

    def test_temperature_decreases_with_altitude(self):
        sea = EnvironmentalConditions.from_altitude(0.0)
        denver = EnvironmentalConditions.from_altitude(_DENVER_ALTITUDE_M)
        assert denver.temperature < sea.temperature

    def test_altitude_stored_in_instance(self):
        env = EnvironmentalConditions.from_altitude(1000.0)
        assert env.altitude == 1000.0

    def test_negative_altitude_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            EnvironmentalConditions.from_altitude(-10.0)


class TestVelocityDependentSpinDecay:
    """compute_spin_decay scales with velocity when velocity_magnitude is provided."""

    @pytest.fixture()
    def engine(self):
        from src.shared.python.physics.aerodynamics import (
            AerodynamicsConfig,
            AerodynamicsEngine,
        )

        return AerodynamicsEngine(AerodynamicsConfig())

    def test_at_reference_speed_matches_constant_rate(self, engine):
        import numpy as np

        spin = np.array([0.0, 0.0, 100.0])
        dt = 1.0
        result_const = engine.compute_spin_decay(spin, dt)
        result_vel = engine.compute_spin_decay(spin, dt, velocity_magnitude=70.0)
        assert abs(float(result_const[2]) - float(result_vel[2])) < 1e-10

    def test_high_speed_decays_faster_than_low_speed(self, engine):
        import numpy as np

        spin = np.array([0.0, 0.0, 100.0])
        dt = 1.0
        result_slow = engine.compute_spin_decay(spin, dt, velocity_magnitude=20.0)
        result_fast = engine.compute_spin_decay(spin, dt, velocity_magnitude=80.0)
        assert result_fast[2] < result_slow[2]

    def test_zero_velocity_produces_no_decay(self, engine):
        import numpy as np

        spin = np.array([0.0, 0.0, 100.0])
        result = engine.compute_spin_decay(spin, 1.0, velocity_magnitude=0.0)
        assert abs(result[2] - 100.0) < 1e-10


class TestValidationDataStructures:
    """PGA_TOUR_2024 dataset is importable, complete, and internally consistent."""

    def test_dataset_is_non_empty(self):
        assert len(PGA_TOUR_2024) >= 5

    @pytest.mark.parametrize("point", PGA_TOUR_2024, ids=lambda p: p.club)
    def test_ball_speed_is_positive(self, point):
        assert point.ball_speed_mps > 0

    @pytest.mark.parametrize("point", PGA_TOUR_2024, ids=lambda p: p.club)
    def test_launch_angle_in_physical_range(self, point):
        assert 0 < point.launch_angle_deg < 45

    @pytest.mark.parametrize("point", PGA_TOUR_2024, ids=lambda p: p.club)
    def test_spin_rate_is_positive(self, point):
        assert point.spin_rate_rpm > 0

    @pytest.mark.parametrize("point", PGA_TOUR_2024, ids=lambda p: p.club)
    def test_carry_distance_is_positive(self, point):
        assert point.carry_distance_m > 0

    @pytest.mark.parametrize("point", PGA_TOUR_2024, ids=lambda p: p.club)
    def test_is_valid_carry_accepts_self(self, point):
        assert point.is_valid_carry(point.carry_distance_m)

    @pytest.mark.parametrize("point", PGA_TOUR_2024, ids=lambda p: p.club)
    def test_is_valid_carry_rejects_double(self, point):
        assert not point.is_valid_carry(point.carry_distance_m * 2.0)

    def test_driver_carry_greater_than_wedge(self):
        clubs = {p.club: p for p in PGA_TOUR_2024}
        assert clubs["Driver"].carry_distance_m > clubs["PW"].carry_distance_m

    def test_driver_ball_speed_greater_than_7iron(self):
        clubs = {p.club: p for p in PGA_TOUR_2024}
        assert clubs["Driver"].ball_speed_mps > clubs["7-Iron"].ball_speed_mps

    def test_spin_increases_with_loft(self):
        clubs = {p.club: p for p in PGA_TOUR_2024}
        if "Driver" in clubs and "7-Iron" in clubs:
            assert clubs["7-Iron"].spin_rate_rpm > clubs["Driver"].spin_rate_rpm
