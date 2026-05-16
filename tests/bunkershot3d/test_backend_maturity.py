"""Tests for issue #5486 — fail-loud guards on unimplemented backends.

Both the Chrono and LIGGGHTS BunkerShot3D drivers were stubs that
silently produced no output. The launcher tile presented them as
"ready" alongside the MuJoCo/MPM driver. These tests pin in the
fail-loud behaviour so a regression cannot reintroduce mock data
under the guise of a real simulation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bunkershot3d.backends import BackendNotImplementedError
from bunkershot3d.backends.chrono.driver import ChronoDriver
from bunkershot3d.backends.liggghts.driver import LiggghtsDriver
from bunkershot3d.backends.mpm.driver import MPMDriver
from bunkershot3d.calibration.angle_of_repose import AngleOfReposeExperiment


pytestmark = pytest.mark.unit


@pytest.fixture
def dummy_config(tmp_path: Path) -> Path:
    yaml_content = """
    bunker_bed:
      domain:
        length_x: 2.0
        width_y: 1.0
        depth_z: 0.5
      boundary: "fixed"
    grain_population:
      count: 1000
      diameter_mean: 0.002
      diameter_sigma_log: 0.1
      density: 2650.0
      coarse_graining_factor: 1.0
    contact_model:
      friction_coefficient: 0.5
      restitution_coefficient: 0.3
      youngs_modulus: 1e7
      poisson_ratio: 0.25
    clubhead:
      loft_deg: 56.0
      bounce_deg: 10.0
      width: 0.1
      height: 0.05
      mass: 0.3
    trajectory:
      file: "swing_data.csv"
    output:
      downsample_grains: 10
      rate_hz: 500.0
    """
    config_path = tmp_path / "canonical.yaml"
    config_path.write_text(yaml_content)
    return config_path


def test_backend_not_implemented_error_is_not_implemented_subclass() -> None:
    """The dedicated error should still satisfy ``except NotImplementedError``."""
    assert issubclass(BackendNotImplementedError, NotImplementedError)


def test_chrono_driver_setup_raises(dummy_config: Path) -> None:
    """ChronoDriver.setup must fail loudly until a real implementation lands."""
    driver = ChronoDriver(dummy_config)
    with pytest.raises(BackendNotImplementedError, match="Chrono"):
        driver.setup()


def test_chrono_driver_run_raises(dummy_config: Path, tmp_path: Path) -> None:
    """ChronoDriver.run must also fail loudly (it called setup() internally)."""
    driver = ChronoDriver(dummy_config)
    output_path = tmp_path / "result.h5"
    with pytest.raises(BackendNotImplementedError):
        driver.run(output_path)


def test_liggghts_driver_setup_raises(dummy_config: Path) -> None:
    """LiggghtsDriver.setup must fail loudly until a real implementation lands."""
    driver = LiggghtsDriver(dummy_config)
    with pytest.raises(BackendNotImplementedError, match="LIGGGHTS|Liggghts"):
        driver.setup()


def test_liggghts_driver_run_raises(dummy_config: Path, tmp_path: Path) -> None:
    """LiggghtsDriver.run must also fail loudly."""
    driver = LiggghtsDriver(dummy_config)
    output_path = tmp_path / "result.h5"
    with pytest.raises(BackendNotImplementedError):
        driver.run(output_path)


def test_mpm_driver_real_setup(dummy_config: Path) -> None:
    """The MPM/MuJoCo driver IS real for setup — only the wrench is mocked.

    This pins in that the MPM driver does not regress to raising the
    BackendNotImplementedError; it has a working setup path even though
    contact-wrench extraction is still draft-quality.
    """
    driver = MPMDriver(dummy_config)
    driver.setup()
    assert driver.model is not None
    assert driver.data is not None


def test_angle_of_repose_requires_explicit_mock_kwarg() -> None:
    """The mock formula must be opt-in via ``use_mock=True``.

    Calling ``run_simulation`` with the default path should raise so
    that no consumer accidentally treats the placeholder formula as a
    real simulation result.
    """
    exp = AngleOfReposeExperiment(backend="mock")
    with pytest.raises(NotImplementedError):
        exp.run_simulation({"friction_coefficient": 0.5})


def test_angle_of_repose_mock_formula_is_preserved() -> None:
    """When opted into, the legacy formula is still returned for callers
    that knowingly want a placeholder (the calibration optimizer test)."""
    exp = AngleOfReposeExperiment(backend="mock")
    angle = exp.run_simulation({"friction_coefficient": 0.5}, use_mock=True)
    assert angle == pytest.approx(20.0 + 0.5 * 24.0)


def test_models_yaml_bunkershot_status() -> None:
    """The launcher tile must surface backend maturity as 'experimental'.

    Until the Chrono/LIGGGHTS backends are real, presenting BunkerShot3D
    as ``status: ready`` misrepresents what a user gets when they click
    the tile. ``experimental`` is the existing enum value used elsewhere
    in this file for not-yet-real tools.
    """
    # Locate models.yaml from this test file (repo-relative).
    repo_root = Path(__file__).resolve().parents[2]
    models_yaml = repo_root / "src" / "config" / "models.yaml"
    assert models_yaml.exists(), models_yaml

    data = yaml.safe_load(models_yaml.read_text(encoding="utf-8"))
    models = data.get("models", [])
    bunker = next((m for m in models if m.get("id") == "bunkershot3d"), None)
    assert bunker is not None, "bunkershot3d tile missing from models.yaml"

    launcher = bunker.get("launcher", {})
    assert launcher.get("status") == "experimental", (
        "BunkerShot3D backends are not all real yet — "
        "the launcher tile must be marked 'experimental' (see #5486)."
    )
