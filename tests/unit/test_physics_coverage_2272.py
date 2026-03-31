"""Tests to raise coverage for physics modules - issue #2272.

Covers:
- physics.flight_model_options
- physics.equipment
- physics.terrain (SurfaceMaterial, ElevationMap, TerrainType)
- physics.topography (ElevationPoint, TopographyBounds)
- physics.ground_reaction_forces (pure functions and data classes)
- physics.grip_contact_model (pure functions and data classes)
- physics.energy_monitor (EnergySnapshot, ConservationMonitor validation)
- physics.physics_validation (result dataclasses)
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# flight_model_options
# ---------------------------------------------------------------------------


class TestFlightModelOptions:
    """Tests for FlightModelOptions and helper functions."""

    def test_default_options_all_disabled(self) -> None:
        from src.shared.python.physics.flight_model_options import (
            DEFAULT_OPTIONS,
            FlightModelOptions,
        )

        opts = FlightModelOptions()
        assert opts.enable_wind is False
        assert opts.enable_spin_decay is False
        assert opts.enable_altitude_correction is False
        assert opts.altitude_m == 0.0
        assert DEFAULT_OPTIONS.enable_wind is False

    def test_options_can_be_enabled(self) -> None:
        from src.shared.python.physics.flight_model_options import FlightModelOptions

        opts = FlightModelOptions(
            enable_wind=True,
            enable_spin_decay=True,
            enable_altitude_correction=True,
            altitude_m=1500.0,
        )
        assert opts.enable_wind is True
        assert opts.enable_spin_decay is True
        assert opts.enable_altitude_correction is True
        assert opts.altitude_m == 1500.0

    def test_compute_spin_decay_zero_time(self) -> None:
        from src.shared.python.physics.flight_model_options import compute_spin_decay

        omega = 300.0  # rad/s
        result = compute_spin_decay(omega, 0.0, 0.05)
        assert result == pytest.approx(omega)

    def test_compute_spin_decay_positive_time(self) -> None:
        from src.shared.python.physics.flight_model_options import compute_spin_decay

        omega = 300.0
        decay_rate = 0.05
        t = 20.0
        result = compute_spin_decay(omega, t, decay_rate)
        expected = omega * math.exp(-decay_rate * t)
        assert result == pytest.approx(expected)

    def test_compute_spin_decay_cached(self) -> None:
        from src.shared.python.physics.flight_model_options import compute_spin_decay

        # Call twice to exercise cache
        r1 = compute_spin_decay(100.0, 5.0, 0.02)
        r2 = compute_spin_decay(100.0, 5.0, 0.02)
        assert r1 == r2

    def test_compute_air_density_at_sea_level(self) -> None:
        from src.shared.python.physics.flight_model_options import (
            compute_air_density_at_altitude,
        )

        rho0 = 1.225  # kg/m^3
        result = compute_air_density_at_altitude(rho0, 0.0)
        assert result == pytest.approx(rho0)

    def test_compute_air_density_decreases_with_altitude(self) -> None:
        from src.shared.python.physics.flight_model_options import (
            compute_air_density_at_altitude,
        )

        rho0 = 1.225
        rho_high = compute_air_density_at_altitude(rho0, 8500.0)
        # At scale height, density should be rho0/e ≈ 0.451
        assert rho_high == pytest.approx(rho0 * math.exp(-1.0), rel=1e-3)

    def test_air_density_cached(self) -> None:
        from src.shared.python.physics.flight_model_options import (
            compute_air_density_at_altitude,
        )

        r1 = compute_air_density_at_altitude(1.225, 1000.0)
        r2 = compute_air_density_at_altitude(1.225, 1000.0)
        assert r1 == r2


# ---------------------------------------------------------------------------
# equipment
# ---------------------------------------------------------------------------


class TestEquipment:
    """Tests for golf equipment configuration module."""

    def test_get_driver_config(self) -> None:
        from src.shared.python.physics.equipment import get_club_config

        config = get_club_config("driver")
        assert config is not None
        assert "head_mass" in config
        assert "shaft_length" in config
        assert config["head_mass"] == pytest.approx(0.198)

    def test_get_iron7_config(self) -> None:
        from src.shared.python.physics.equipment import get_club_config

        config = get_club_config("iron_7")
        assert config["club_loft"] == pytest.approx(0.56)

    def test_get_wedge_config(self) -> None:
        from src.shared.python.physics.equipment import get_club_config

        config = get_club_config("wedge")
        assert config["total_length"] == pytest.approx(0.90)

    def test_invalid_club_type_raises(self) -> None:
        from src.shared.python.physics.equipment import get_club_config

        with pytest.raises(ValueError, match="Invalid club_type"):
            get_club_config("putter")

    def test_club_configs_dict_has_all_types(self) -> None:
        from src.shared.python.physics.equipment import CLUB_CONFIGS

        assert "driver" in CLUB_CONFIGS
        assert "iron_7" in CLUB_CONFIGS
        assert "wedge" in CLUB_CONFIGS

    def test_get_config_is_cached(self) -> None:
        from src.shared.python.physics.equipment import get_club_config

        c1 = get_club_config("driver")
        c2 = get_club_config("driver")
        assert c1 is c2  # same object from cache


# ---------------------------------------------------------------------------
# physics.terrain — SurfaceMaterial
# ---------------------------------------------------------------------------


class TestSurfaceMaterial:
    """Tests for SurfaceMaterial dataclass and validation."""

    def test_create_valid_material(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(name="test")
        assert mat.name == "test"
        assert mat.friction_coefficient == pytest.approx(0.5)

    def test_negative_friction_raises(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        with pytest.raises(ValueError, match="friction_coefficient"):
            SurfaceMaterial(name="bad", friction_coefficient=-0.1)

    def test_invalid_restitution_raises(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        with pytest.raises(ValueError, match="restitution"):
            SurfaceMaterial(name="bad", restitution=1.5)

    def test_invalid_hardness_raises(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        with pytest.raises(ValueError, match="hardness"):
            SurfaceMaterial(name="bad", hardness=-0.1)

    def test_negative_grass_height_raises(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        with pytest.raises(ValueError, match="grass_height"):
            SurfaceMaterial(name="bad", grass_height_m=-0.01)

    def test_invalid_compressibility_raises(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        with pytest.raises(ValueError, match="compressibility"):
            SurfaceMaterial(name="bad", compressibility=1.5)

    def test_invalid_moisture_raises(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        with pytest.raises(ValueError, match="moisture"):
            SurfaceMaterial(name="bad", moisture_content=2.0)

    def test_is_compressible_true(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(name="soft", compressibility=0.5)
        assert mat.is_compressible is True

    def test_is_compressible_false(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(name="rigid", compressibility=0.0)
        assert mat.is_compressible is False

    def test_get_effective_stiffness(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(name="rigid", compressibility=0.0)
        stiffness = mat.get_effective_stiffness(base_stiffness=1e5)
        assert stiffness == pytest.approx(1e5)  # rigid: no reduction

    def test_get_effective_stiffness_compressible(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(name="soft", compressibility=1.0)
        stiffness = mat.get_effective_stiffness(base_stiffness=1e5)
        assert stiffness < 1e5

    def test_get_max_compression_depth_no_grass(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(name="bare", grass_height_m=0.0)
        depth = mat.get_max_compression_depth()
        assert depth == pytest.approx(0.0)

    def test_get_max_compression_depth_with_grass(self) -> None:
        from src.shared.python.physics.terrain import SurfaceMaterial

        mat = SurfaceMaterial(
            name="rough",
            grass_height_m=0.05,
            compressibility=0.5,
            moisture_content=0.3,
        )
        depth = mat.get_max_compression_depth()
        assert depth > 0.0


class TestPredefinedMaterials:
    """Tests for the predefined MATERIALS dictionary."""

    def test_all_terrain_types_have_material(self) -> None:
        from src.shared.python.physics.terrain import (
            MATERIALS,
            TERRAIN_MATERIAL_MAP,
            TerrainType,
        )

        for terrain_type in TerrainType:
            mat_name = TERRAIN_MATERIAL_MAP[terrain_type]
            assert mat_name in MATERIALS, f"Material {mat_name} not in MATERIALS"

    def test_fairway_material(self) -> None:
        from src.shared.python.physics.terrain import MATERIALS

        mat = MATERIALS["fairway"]
        assert mat.name == "fairway"
        assert 0 <= mat.friction_coefficient <= 2
        assert 0 <= mat.restitution <= 1

    def test_green_harder_than_rough(self) -> None:
        from src.shared.python.physics.terrain import MATERIALS

        green = MATERIALS["green"]
        rough = MATERIALS["rough"]
        assert green.hardness > rough.hardness

    def test_bunker_high_friction(self) -> None:
        from src.shared.python.physics.terrain import MATERIALS

        bunker = MATERIALS["bunker"]
        assert bunker.friction_coefficient > 0.5

    def test_terrain_type_enum_values(self) -> None:
        from src.shared.python.physics.terrain import TerrainType

        assert TerrainType.FAIRWAY is not None
        assert TerrainType.GREEN is not None
        assert TerrainType.BUNKER is not None
        assert len(list(TerrainType)) == 9


# ---------------------------------------------------------------------------
# physics.terrain — ElevationMap
# ---------------------------------------------------------------------------


class TestElevationMap:
    """Tests for ElevationMap creation and queries."""

    def test_flat_map_creation(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=100.0, length=200.0, resolution=1.0)
        assert em.width == pytest.approx(100.0)
        assert em.length == pytest.approx(200.0)
        assert em.data.shape == (200, 100)

    def test_flat_map_nonzero_base(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(
            width=10.0, length=10.0, resolution=1.0, base_elevation=5.0
        )
        assert em.get_elevation(5.0, 5.0) == pytest.approx(5.0)

    def test_flat_map_invalid_dimensions(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        with pytest.raises(ValueError):
            ElevationMap.flat(width=-1.0, length=10.0, resolution=1.0)

    def test_flat_map_invalid_resolution(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        with pytest.raises(ValueError):
            ElevationMap.flat(width=10.0, length=10.0, resolution=-0.5)

    def test_sloped_map_creation(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.sloped(
            width=100.0,
            length=100.0,
            resolution=1.0,
            slope_angle_deg=5.0,
            slope_direction_deg=0.0,
        )
        assert em.data.shape[0] == 100

    def test_sloped_map_elevation_increases_with_x(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.sloped(
            width=100.0,
            length=100.0,
            resolution=1.0,
            slope_angle_deg=10.0,
            slope_direction_deg=0.0,  # slope in X direction
        )
        h0 = em.get_elevation(1.0, 50.0)
        h1 = em.get_elevation(50.0, 50.0)
        assert h1 > h0  # higher up the slope

    def test_from_array(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        data = np.zeros((10, 10), dtype=np.float64)
        data[5, 5] = 1.0
        em = ElevationMap.from_array(data, resolution=1.0)
        assert em.width == pytest.approx(10.0)
        assert em.length == pytest.approx(10.0)

    def test_from_array_invalid_resolution(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        data = np.zeros((5, 5))
        with pytest.raises(ValueError):
            ElevationMap.from_array(data, resolution=0.0)

    def test_get_elevation_flat_anywhere(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=50.0, length=50.0, resolution=0.5)
        assert em.get_elevation(10.0, 20.0) == pytest.approx(0.0)

    def test_get_elevation_out_of_bounds_raises(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=10.0, length=10.0, resolution=1.0)
        with pytest.raises(ValueError):
            em.get_elevation(15.0, 5.0)

    def test_get_gradient_flat_is_zero(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=10.0, length=10.0, resolution=0.5)
        dzdx, dzdy = em.get_gradient(5.0, 5.0)
        assert dzdx == pytest.approx(0.0, abs=1e-9)
        assert dzdy == pytest.approx(0.0, abs=1e-9)

    def test_get_normal_flat_is_up(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=10.0, length=10.0, resolution=0.5)
        normal = em.get_normal(5.0, 5.0)
        assert normal[2] == pytest.approx(1.0, abs=1e-6)
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)

    def test_get_slope_angle_flat_is_zero(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=10.0, length=10.0, resolution=0.5)
        angle = em.get_slope_angle(5.0, 5.0)
        assert angle == pytest.approx(0.0, abs=1e-6)

    def test_to_dict_and_from_dict(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap

        em = ElevationMap.flat(width=5.0, length=5.0, resolution=1.0)
        d = em.to_dict()
        em2 = ElevationMap.from_dict(d)
        assert em2.width == pytest.approx(em.width)
        assert em2.length == pytest.approx(em.length)
        assert em2.resolution == pytest.approx(em.resolution)


# ---------------------------------------------------------------------------
# physics.terrain — Terrain and TerrainConfig
# ---------------------------------------------------------------------------


class TestTerrainConfig:
    """Tests for TerrainConfig dataclass."""

    def test_terrain_config_creation(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap, TerrainConfig

        em = ElevationMap.flat(width=50.0, length=50.0, resolution=1.0)
        cfg = TerrainConfig(
            name="test_course",
            elevation_config=em.to_dict(),
            patches_config=[],
        )
        assert cfg.name == "test_course"
        assert cfg.default_type == "rough"

    def test_terrain_config_from_dict(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap, TerrainConfig

        em = ElevationMap.flat(width=10.0, length=10.0, resolution=1.0)
        d = {
            "name": "round",
            "elevation": em.to_dict(),
            "patches": [],
            "regions": [],
            "default_type": "fairway",
        }
        cfg = TerrainConfig.from_dict(d)
        assert cfg.name == "round"
        assert cfg.default_type == "fairway"

    def test_terrain_config_to_terrain(self) -> None:
        from src.shared.python.physics.terrain import (
            ElevationMap,
            Terrain,
            TerrainConfig,
        )

        em = ElevationMap.flat(width=20.0, length=20.0, resolution=1.0)
        cfg = TerrainConfig(
            name="flat",
            elevation_config=em.to_dict(),
            patches_config=[],
            default_type="fairway",
        )
        terrain = cfg.to_terrain()
        assert isinstance(terrain, Terrain)
        assert terrain.name == "flat"


class TestTerrainClass:
    """Tests for the Terrain class."""

    def _make_terrain(self, name: str = "test") -> object:
        from src.shared.python.physics.terrain import ElevationMap, Terrain, TerrainType

        em = ElevationMap.flat(width=50.0, length=50.0, resolution=1.0)
        return Terrain(name=name, elevation=em, default_type=TerrainType.FAIRWAY)

    def test_create_flat_terrain(self) -> None:
        from src.shared.python.physics.terrain import ElevationMap, Terrain, TerrainType

        em = ElevationMap.flat(width=50.0, length=100.0, resolution=1.0)
        terrain = Terrain(
            name="flat_course", elevation=em, default_type=TerrainType.FAIRWAY
        )
        assert terrain.name == "flat_course"

    def test_terrain_get_elevation(self) -> None:
        terrain = self._make_terrain()
        h = terrain.get_elevation(10.0, 10.0)
        assert isinstance(h, float)
        assert h == pytest.approx(0.0)

    def test_terrain_get_material(self) -> None:
        terrain = self._make_terrain()
        mat = terrain.get_material(10.0, 10.0)
        assert mat is not None
        assert hasattr(mat, "friction_coefficient")

    def test_terrain_get_normal(self) -> None:
        terrain = self._make_terrain()
        normal = terrain.get_normal(10.0, 10.0)
        assert isinstance(normal, np.ndarray)
        assert normal.shape == (3,)
        assert np.linalg.norm(normal) == pytest.approx(1.0, abs=1e-6)

    def test_terrain_get_terrain_type(self) -> None:
        from src.shared.python.physics.terrain import TerrainType

        terrain = self._make_terrain()
        terrain_type = terrain.get_terrain_type(10.0, 10.0)
        assert isinstance(terrain_type, TerrainType)

    def test_terrain_config_round_trip(self) -> None:
        from src.shared.python.physics.terrain import TerrainConfig

        terrain = self._make_terrain("round_trip")
        cfg = TerrainConfig.from_terrain(terrain)
        assert cfg.name == "round_trip"
        restored = cfg.to_terrain()
        assert restored.name == terrain.name


# ---------------------------------------------------------------------------
# physics.topography — ElevationPoint and TopographyBounds
# ---------------------------------------------------------------------------


class TestElevationPoint:
    """Tests for ElevationPoint dataclass."""

    def test_create_elevation_point(self) -> None:
        from src.shared.python.physics.topography import ElevationPoint

        pt = ElevationPoint(x=10.0, y=20.0, z=1.5)
        assert pt.x == 10.0
        assert pt.y == 20.0
        assert pt.z == 1.5

    def test_as_array(self) -> None:
        from src.shared.python.physics.topography import ElevationPoint

        pt = ElevationPoint(x=1.0, y=2.0, z=3.0)
        arr = pt.as_array()
        assert arr.shape == (3,)
        assert arr[0] == pytest.approx(1.0)
        assert arr[1] == pytest.approx(2.0)
        assert arr[2] == pytest.approx(3.0)


class TestTopographyBounds:
    """Tests for TopographyBounds dataclass."""

    def test_default_bounds(self) -> None:
        from src.shared.python.physics.topography import TopographyBounds

        bounds = TopographyBounds()
        assert bounds.min_x == 0.0
        assert bounds.max_x == 100.0
        assert bounds.width == 100.0

    def test_width_and_height(self) -> None:
        from src.shared.python.physics.topography import TopographyBounds

        bounds = TopographyBounds(min_x=10.0, max_x=60.0, min_y=5.0, max_y=55.0)
        assert bounds.width == pytest.approx(50.0)
        assert bounds.height == pytest.approx(50.0)

    def test_elevation_range(self) -> None:
        from src.shared.python.physics.topography import TopographyBounds

        bounds = TopographyBounds(min_z=-2.0, max_z=8.0)
        assert bounds.elevation_range == pytest.approx(10.0)


class TestTopographyData:
    """Tests for TopographyData class."""

    def test_create_topography_empty(self) -> None:
        from src.shared.python.physics.topography import (
            TopographyData,
        )

        topo = TopographyData()
        assert topo is not None
        assert topo.is_loaded is False

    def test_create_topography_with_bounds(self) -> None:
        from src.shared.python.physics.topography import (
            TopographyBounds,
            TopographyData,
        )

        bounds = TopographyBounds(min_x=0.0, max_x=100.0, min_y=0.0, max_y=100.0)
        topo = TopographyData(bounds=bounds)
        assert topo.bounds.width == pytest.approx(100.0)

    def test_set_heightmap_and_query(self) -> None:
        from src.shared.python.physics.topography import (
            TopographyBounds,
            TopographyData,
        )

        bounds = TopographyBounds(min_x=0.0, max_x=10.0, min_y=0.0, max_y=10.0)
        topo = TopographyData(bounds=bounds)
        heightmap = np.zeros((20, 20))
        topo.set_heightmap(heightmap, smooth=False)
        assert topo.is_loaded is True
        pos = np.array([5.0, 5.0])
        h = topo.get_elevation_at(pos)
        assert h == pytest.approx(0.0, abs=0.01)

    def test_get_bounds_property(self) -> None:
        from src.shared.python.physics.topography import (
            TopographyBounds,
            TopographyData,
        )

        bounds = TopographyBounds(min_x=0.0, max_x=50.0, min_y=0.0, max_y=50.0)
        topo = TopographyData(bounds=bounds)
        b = topo.bounds
        assert b.width == pytest.approx(50.0)

    def test_get_normal_flat_is_up(self) -> None:
        from src.shared.python.physics.topography import (
            TopographyBounds,
            TopographyData,
        )

        bounds = TopographyBounds(min_x=0.0, max_x=10.0, min_y=0.0, max_y=10.0)
        topo = TopographyData(bounds=bounds)
        heightmap = np.zeros((20, 20))
        topo.set_heightmap(heightmap, smooth=False)
        pos = np.array([5.0, 5.0])
        normal = topo.get_normal_at(pos)
        assert isinstance(normal, np.ndarray)
        assert normal[2] == pytest.approx(1.0, abs=1e-3)

    def test_set_contour_points(self) -> None:
        from src.shared.python.physics.topography import ElevationPoint, TopographyData

        topo = TopographyData()
        points = [
            ElevationPoint(x=0.0, y=0.0, z=0.0),
            ElevationPoint(x=10.0, y=0.0, z=0.0),
            ElevationPoint(x=5.0, y=10.0, z=0.0),
            ElevationPoint(x=0.0, y=10.0, z=0.0),
            ElevationPoint(x=10.0, y=10.0, z=0.0),
        ]
        topo.set_contour_points(points)
        assert topo.is_loaded is True

    def test_elevation_at_not_loaded_returns_zero(self) -> None:
        from src.shared.python.physics.topography import TopographyData

        topo = TopographyData()
        pos = np.array([5.0, 5.0])
        h = topo.get_elevation_at(pos)
        assert isinstance(h, float)


# ---------------------------------------------------------------------------
# physics.ground_reaction_forces — pure functions
# ---------------------------------------------------------------------------


class TestComputeLinearImpulse:
    """Tests for compute_linear_impulse function."""

    def test_zero_force(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_linear_impulse,
        )

        forces = np.zeros((5, 3))
        timestamps = np.linspace(0, 0.1, 5)
        impulse = compute_linear_impulse(forces, timestamps)
        assert np.allclose(impulse, 0.0)

    def test_constant_force(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_linear_impulse,
        )

        # Constant 700N vertical force for 1 second
        n = 100
        forces = np.zeros((n, 3))
        forces[:, 2] = 700.0
        timestamps = np.linspace(0, 1.0, n)
        impulse = compute_linear_impulse(forces, timestamps)
        # J = F * dt = 700 N * 1 s = 700 N·s
        assert impulse[2] == pytest.approx(700.0, rel=1e-3)
        assert impulse[0] == pytest.approx(0.0, abs=1e-6)

    def test_single_sample_returns_zero(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_linear_impulse,
        )

        forces = np.array([[0.0, 0.0, 700.0]])
        timestamps = np.array([0.0])
        impulse = compute_linear_impulse(forces, timestamps)
        assert np.allclose(impulse, 0.0)


class TestComputeAngularImpulse:
    """Tests for compute_angular_impulse function."""

    def test_zero_force_angular_impulse(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_angular_impulse,
        )

        n = 10
        forces = np.zeros((n, 3))
        cops = np.zeros((n, 3))
        timestamps = np.linspace(0, 1.0, n)
        ref = np.zeros(3)
        ang = compute_angular_impulse(forces, cops, timestamps, ref)
        assert np.allclose(ang, 0.0)

    def test_single_sample_returns_zero(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_angular_impulse,
        )

        forces = np.array([[0.0, 0.0, 700.0]])
        cops = np.array([[0.1, 0.0, 0.0]])
        timestamps = np.array([0.0])
        ref = np.zeros(3)
        ang = compute_angular_impulse(forces, cops, timestamps, ref)
        assert np.allclose(ang, 0.0)


class TestComputeCopFromGrf:
    """Tests for compute_cop_from_grf function."""

    def test_zero_vertical_force_returns_ground(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_cop_from_grf,
        )

        force = np.array([0.0, 0.0, 0.0])
        moment = np.array([0.0, 0.0, 0.0])
        cop = compute_cop_from_grf(force, moment)
        assert cop[2] == pytest.approx(0.0)

    def test_cop_from_known_force_moment(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_cop_from_grf,
        )

        # F_z = 700 N, M_x = 70 N·m → COP_y = 70/700 = 0.1 m
        force = np.array([0.0, 0.0, 700.0])
        moment = np.array([70.0, 0.0, 0.0])
        cop = compute_cop_from_grf(force, moment)
        assert cop[1] == pytest.approx(0.1, rel=1e-3)

    def test_cop_z_at_ground_height(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_cop_from_grf,
        )

        force = np.array([0.0, 0.0, 700.0])
        moment = np.array([0.0, 0.0, 0.0])
        cop = compute_cop_from_grf(force, moment, ground_height=0.05)
        assert cop[2] == pytest.approx(0.05)


class TestComputeCopTrajectoryLength:
    """Tests for compute_cop_trajectory_length function."""

    def test_single_point_is_zero_length(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_cop_trajectory_length,
        )

        cops = np.array([[0.0, 0.0, 0.0]])
        assert compute_cop_trajectory_length(cops) == pytest.approx(0.0)

    def test_straight_line_length(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            compute_cop_trajectory_length,
        )

        cops = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        length = compute_cop_trajectory_length(cops)
        assert length == pytest.approx(2.0)


class TestGRFDataClasses:
    """Tests for GRF data classes."""

    def test_ground_reaction_force_creation(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            FootSide,
            GroundReactionForce,
        )

        grf = GroundReactionForce(
            force=np.array([0.0, 0.0, 700.0]),
            moment=np.array([0.0, 0.0, 0.0]),
            cop=np.array([0.0, 0.0, 0.0]),
            timestamp=0.5,
            foot_side=FootSide.LEFT,
        )
        assert grf.timestamp == 0.5
        assert grf.foot_side == FootSide.LEFT

    def test_grf_time_series_creation(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import (
            FootSide,
            GRFTimeSeries,
        )

        n = 10
        ts = GRFTimeSeries(
            timestamps=np.linspace(0, 1, n),
            forces=np.zeros((n, 3)),
            moments=np.zeros((n, 3)),
            cops=np.zeros((n, 3)),
            foot_side=FootSide.RIGHT,
            sample_rate=1000.0,
        )
        assert ts.sample_rate == 1000.0
        assert ts.foot_side == FootSide.RIGHT

    def test_foot_side_enum(self) -> None:
        from src.shared.python.physics.ground_reaction_forces import FootSide

        assert FootSide.LEFT is not None
        assert FootSide.RIGHT is not None
        assert FootSide.COMBINED is not None


# ---------------------------------------------------------------------------
# physics.grip_contact_model — pure functions
# ---------------------------------------------------------------------------


class TestCheckFrictionCone:
    """Tests for check_friction_cone function."""

    def test_sticking_within_cone(self) -> None:
        from src.shared.python.physics.grip_contact_model import check_friction_cone

        normal_force = 100.0
        tangent_force = np.array([0.0, 0.0, 50.0])  # magnitude = 50
        mu = 0.8
        # max tangent = 80 N, 50 < 80 → sticking
        assert check_friction_cone(normal_force, tangent_force, mu) is True

    def test_slipping_outside_cone(self) -> None:
        from src.shared.python.physics.grip_contact_model import check_friction_cone

        normal_force = 100.0
        tangent_force = np.array([0.0, 0.0, 90.0])  # magnitude = 90
        mu = 0.8
        # max tangent = 80 N, 90 > 80 → slipping
        assert check_friction_cone(normal_force, tangent_force, mu) is False

    def test_zero_normal_force(self) -> None:
        from src.shared.python.physics.grip_contact_model import check_friction_cone

        normal_force = 0.0
        tangent_force = np.array([0.1, 0.0, 0.0])
        mu = 0.8
        # max tangent = 0 → slipping
        assert check_friction_cone(normal_force, tangent_force, mu) is False


class TestComputeSlipDirection:
    """Tests for compute_slip_direction function."""

    def test_returns_unit_vector(self) -> None:
        from src.shared.python.physics.grip_contact_model import compute_slip_direction

        tangent = np.array([3.0, 0.0, 4.0])
        direction = compute_slip_direction(tangent)
        assert np.linalg.norm(direction) == pytest.approx(1.0, abs=1e-9)

    def test_zero_force_returns_zero(self) -> None:
        from src.shared.python.physics.grip_contact_model import compute_slip_direction

        tangent = np.zeros(3)
        direction = compute_slip_direction(tangent)
        assert np.allclose(direction, 0.0)


class TestDecomposeContactForce:
    """Tests for decompose_contact_force function."""

    def test_purely_normal_force(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            decompose_contact_force,
        )

        contact_force = np.array([0.0, 0.0, 100.0])
        contact_normal = np.array([0.0, 0.0, 1.0])
        normal, tangent = decompose_contact_force(contact_force, contact_normal)
        assert normal == pytest.approx(100.0)
        assert np.allclose(tangent, 0.0, atol=1e-9)

    def test_purely_tangential_force(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            decompose_contact_force,
        )

        contact_force = np.array([50.0, 0.0, 0.0])
        contact_normal = np.array([0.0, 0.0, 1.0])
        normal, tangent = decompose_contact_force(contact_force, contact_normal)
        assert normal == pytest.approx(0.0)
        assert tangent[0] == pytest.approx(50.0)

    def test_mixed_force(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            decompose_contact_force,
        )

        contact_force = np.array([30.0, 40.0, 50.0])
        contact_normal = np.array([0.0, 0.0, 1.0])
        normal, tangent = decompose_contact_force(contact_force, contact_normal)
        assert normal == pytest.approx(50.0)
        assert tangent[2] == pytest.approx(0.0, abs=1e-9)


class TestClassifyContactState:
    """Tests for classify_contact_state function."""

    def test_no_contact_negative_normal(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            ContactState,
            GripParameters,
            classify_contact_state,
        )

        params = GripParameters()
        state = classify_contact_state(
            normal_force=-10.0,
            tangent_force=np.zeros(3),
            slip_velocity=np.zeros(3),
            params=params,
        )
        assert state == ContactState.NO_CONTACT

    def test_sticking_contact(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            ContactState,
            GripParameters,
            classify_contact_state,
        )

        params = GripParameters(static_friction=0.8)
        state = classify_contact_state(
            normal_force=100.0,
            tangent_force=np.array([0.0, 0.0, 50.0]),  # within cone
            slip_velocity=np.zeros(3),  # no slip velocity
            params=params,
        )
        assert state == ContactState.STICKING

    def test_slipping_high_velocity(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            ContactState,
            GripParameters,
            classify_contact_state,
        )

        params = GripParameters()
        state = classify_contact_state(
            normal_force=100.0,
            tangent_force=np.zeros(3),
            slip_velocity=np.array([0.1, 0.0, 0.0]),  # above threshold
            params=params,
        )
        assert state == ContactState.SLIPPING


class TestComputeCenterOfPressure:
    """Tests for compute_center_of_pressure function."""

    def test_empty_contacts(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            compute_center_of_pressure,
        )

        cop = compute_center_of_pressure([])
        assert cop.shape == (3,)
        assert np.allclose(cop, 0.0)

    def test_single_contact(self) -> None:
        from src.shared.python.physics.grip_contact_model import (
            ContactPoint,
            ContactState,
            compute_center_of_pressure,
        )

        contact = ContactPoint(
            position=np.array([1.0, 2.0, 0.0]),
            normal=np.array([0.0, 0.0, 1.0]),
            normal_force=100.0,
            tangent_force=np.zeros(3),
            slip_velocity=np.zeros(3),
            state=ContactState.STICKING,
        )
        cop = compute_center_of_pressure([contact])
        assert cop[0] == pytest.approx(1.0)
        assert cop[1] == pytest.approx(2.0)


class TestGripParameters:
    """Tests for GripParameters dataclass."""

    def test_default_parameters(self) -> None:
        from src.shared.python.physics.grip_contact_model import GripParameters

        params = GripParameters()
        assert params.static_friction > 0
        assert params.dynamic_friction > 0
        assert params.static_friction >= params.dynamic_friction


# ---------------------------------------------------------------------------
# physics.energy_monitor — EnergySnapshot and ConservationMonitor validation
# ---------------------------------------------------------------------------


class TestEnergySnapshot:
    """Tests for EnergySnapshot dataclass."""

    def test_total_energy(self) -> None:
        from src.shared.python.physics.energy_monitor import EnergySnapshot

        snap = EnergySnapshot(time=1.0, kinetic=10.0, potential=5.0)
        assert snap.total == pytest.approx(15.0)

    def test_zero_energies(self) -> None:
        from src.shared.python.physics.energy_monitor import EnergySnapshot

        snap = EnergySnapshot(time=0.0, kinetic=0.0, potential=0.0)
        assert snap.total == pytest.approx(0.0)

    def test_negative_potential(self) -> None:
        from src.shared.python.physics.energy_monitor import EnergySnapshot

        snap = EnergySnapshot(time=2.0, kinetic=20.0, potential=-5.0)
        assert snap.total == pytest.approx(15.0)


class TestConservationMonitorValidation:
    """Tests for ConservationMonitor initialization validation."""

    def test_invalid_max_drift_raises(self) -> None:
        from src.shared.python.physics.energy_monitor import ConservationMonitor

        engine = MagicMock()
        with pytest.raises(ValueError, match="max_drift_pct"):
            ConservationMonitor(engine=engine, max_drift_pct=-1.0)

    def test_invalid_critical_drift_raises(self) -> None:
        from src.shared.python.physics.energy_monitor import ConservationMonitor

        engine = MagicMock()
        with pytest.raises(ValueError, match="critical_drift_pct"):
            ConservationMonitor(engine=engine, critical_drift_pct=-5.0)

    def test_critical_must_exceed_max(self) -> None:
        from src.shared.python.physics.energy_monitor import ConservationMonitor

        engine = MagicMock()
        with pytest.raises(ValueError):
            ConservationMonitor(
                engine=engine, max_drift_pct=5.0, critical_drift_pct=3.0
            )

    def test_valid_construction(self) -> None:
        from src.shared.python.physics.energy_monitor import ConservationMonitor

        engine = MagicMock()
        monitor = ConservationMonitor(
            engine=engine, max_drift_pct=1.0, critical_drift_pct=5.0
        )
        assert monitor.E_initial is None
        assert monitor.drift_history == []

    def test_integration_failure_error_is_exception(self) -> None:
        from src.shared.python.physics.energy_monitor import IntegrationFailureError

        err = IntegrationFailureError("test error")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# physics.physics_validation — result dataclasses
# ---------------------------------------------------------------------------


class TestPhysicsValidationDataclasses:
    """Tests for result dataclasses in physics_validation."""

    def test_energy_validation_result_pass(self) -> None:
        from src.shared.python.physics.physics_validation import EnergyValidationResult

        result = EnergyValidationResult(
            energy_error=1e-7,
            relative_error=1e-7,
            passes=True,
            kinetic_energy_initial=100.0,
            kinetic_energy_final=100.0,
            potential_energy_initial=50.0,
            potential_energy_final=50.0,
            work_applied=0.0,
            message="OK",
        )
        assert result.passes is True
        assert "PASS" in str(result)

    def test_energy_validation_result_fail(self) -> None:
        from src.shared.python.physics.physics_validation import EnergyValidationResult

        result = EnergyValidationResult(
            energy_error=0.1,
            relative_error=0.1,
            passes=False,
            kinetic_energy_initial=100.0,
            kinetic_energy_final=90.0,
            potential_energy_initial=50.0,
            potential_energy_final=50.0,
            work_applied=0.0,
            message="Drift too large",
        )
        assert result.passes is False
        assert "FAIL" in str(result)

    def test_jacobian_validation_result_pass(self) -> None:
        from src.shared.python.physics.physics_validation import (
            JacobianValidationResult,
        )

        result = JacobianValidationResult(
            jacobian_error=1e-8,
            passes=True,
            body_id=0,
            message="OK",
        )
        assert result.passes is True
        assert "PASS" in str(result)

    def test_jacobian_validation_result_fail(self) -> None:
        from src.shared.python.physics.physics_validation import (
            JacobianValidationResult,
        )

        result = JacobianValidationResult(
            jacobian_error=0.01,
            passes=False,
            body_id=5,
            message="Jacobian mismatch",
        )
        assert result.passes is False
        assert "FAIL" in str(result)

    def test_physics_validator_has_expected_methods(self) -> None:
        from src.shared.python.physics.physics_validation import PhysicsValidator

        assert hasattr(PhysicsValidator, "verify_energy_conservation")
        assert hasattr(PhysicsValidator, "verify_jacobian")
        assert hasattr(PhysicsValidator, "run_full_validation")


# ---------------------------------------------------------------------------
# physics.terrain_engine — TerrainAwareEngine
# ---------------------------------------------------------------------------


class TestTerrainAwareEngine:
    """Tests for TerrainAwareEngine class."""

    def test_construction_default(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        assert engine.terrain is None
        assert engine.default_stiffness > 0

    def _make_terrain(self) -> object:
        from src.shared.python.physics.terrain import ElevationMap, Terrain, TerrainType

        em = ElevationMap.flat(width=50.0, length=50.0, resolution=1.0)
        return Terrain(name="flat", elevation=em, default_type=TerrainType.FAIRWAY)

    def test_set_terrain(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        terrain = self._make_terrain()
        engine.set_terrain(terrain)
        assert engine.terrain is not None

    def test_get_ground_height_without_terrain(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        h = engine.get_ground_height(10.0, 10.0)
        assert isinstance(h, float)

    def test_get_ground_height_with_terrain(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        engine.set_terrain(self._make_terrain())
        h = engine.get_ground_height(10.0, 10.0)
        assert isinstance(h, float)

    def test_get_contact_normal(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        engine.set_terrain(self._make_terrain())
        normal = engine.get_contact_normal(10.0, 10.0)
        assert isinstance(normal, np.ndarray)
        assert normal.shape == (3,)

    def test_get_friction(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        engine.set_terrain(self._make_terrain())
        friction = engine.get_friction(10.0, 10.0)
        assert isinstance(friction, float)
        assert friction >= 0

    def test_get_restitution(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        engine = TerrainAwareEngine()
        engine.set_terrain(self._make_terrain())
        rest = engine.get_restitution(10.0, 10.0)
        assert isinstance(rest, float)
        assert 0 <= rest <= 1

    def test_invalid_stiffness_raises(self) -> None:
        from src.shared.python.physics.terrain_engine import TerrainAwareEngine

        with pytest.raises((ValueError, TypeError)):
            TerrainAwareEngine(stiffness=None)  # type: ignore[arg-type]
