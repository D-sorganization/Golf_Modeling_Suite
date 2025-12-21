"""Physics validation tests verifying energy conservation."""

import logging

import numpy as np
import pytest

from shared.python.engine_manager import EngineManager, EngineType
from tests.physics_validation.analytical import AnalyticalBallistic

logger = logging.getLogger(__name__)


def is_engine_available(engine_type: EngineType) -> bool:
    """Check if an engine is installed and importable."""
    manager = EngineManager()
    probe_result = manager.get_probe_result(engine_type)
    return probe_result.is_available()


@pytest.mark.skipif(
    not is_engine_available(EngineType.MUJOCO), reason="MuJoCo not installed"
)
def test_mujoco_ballistic_energy_conservation():
    """Verify energy conservation for a falling particle in MuJoCo."""
    import mujoco

    # 1. Setup Simulation
    # Define a simple XML model: a particle falling under gravity
    xml = """
    <mujoco>
        <option timestep="0.001" gravity="0 0 -9.81" integrator="RK4"/>
        <worldbody>
            <body name="ball" pos="0 0 10">
                <joint type="free"/>
                <geom type="sphere" size="0.1" mass="1.0"/>
            </body>
        </worldbody>
    </mujoco>
    """

    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    # Analytical Solver
    baseline = AnalyticalBallistic(mass=1.0, g=9.81)

    # Initial State
    mujoco.mj_resetData(model, data)
    initial_energy = baseline.total_energy(height=10.0, velocity=0.0)

    # Run Simulation for 1 second
    steps = 1000
    energies = []

    for _ in range(steps):
        mujoco.mj_step(model, data)

        # Get state
        height = data.qpos[2]  # z position (free joint: x,y,z, qw,qx,qy,qz)

        # Velocity magnitude
        # qvel has 6 DOFs for free joint: vx, vy, vz, wx, wy, wz
        viz = data.qvel[2]
        velocity = abs(viz)

        # Calculate Energy
        current_energy = baseline.total_energy(height, velocity)
        energies.append(current_energy)

    # Validation
    # Energy should be conserved (numerical error only)
    # Allow 0.1% error for RK4 integration
    max_deviation = np.max(np.abs(np.array(energies) - initial_energy))
    percent_error = (max_deviation / initial_energy) * 100

    logger.info(f"MuJoCo Ballistic Energy Error: {percent_error:.4f}%")
    assert percent_error < 0.1, f"Energy not conserved! Error: {percent_error:.4f}%"


@pytest.mark.skipif(
    not is_engine_available(EngineType.PINOCCHIO), reason="Pinocchio not installed"
)
def test_pinocchio_energy_check():
    """Placeholder for Pinocchio energy validation."""
    # Logic similar to above but using Pinocchio API
    pass
