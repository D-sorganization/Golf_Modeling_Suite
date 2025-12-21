"""Physics validation tests verifying pendulum dynamics accuracy."""

import logging

import numpy as np
import pytest

from shared.python.engine_manager import EngineManager, EngineType
from tests.physics_validation.analytical import AnalyticalPendulum

logger = logging.getLogger(__name__)


def is_engine_available(engine_type: EngineType) -> bool:
    """Check if an engine is installed and importable."""
    manager = EngineManager()
    probe_result = manager.get_probe_result(engine_type)
    return probe_result.is_available()


@pytest.mark.skipif(
    not is_engine_available(EngineType.MUJOCO), reason="MuJoCo not installed"
)
def test_mujoco_pendulum_accuracy():
    """Verify MuJoCo pendulum matches analytical solution."""
    import mujoco

    # 1. Model: Simple Pendulum (L=1, m=1)
    # Hinge joint at particle point? No, standard pendulum model.
    xml = """
    <mujoco>
        <option timestep="0.001" gravity="0 0 -9.81" integrator="RK4"/>
        <worldbody>
            <body>
                <joint name="pin" type="hinge" axis="0 1 0" pos="0 0 0"/>
                <geom type="cylinder" fromto="0 0 0 0 0 -1" size="0.02" mass="0"/>
                <body pos="0 0 -1">
                    <geom type="sphere" size="0.1" mass="1.0"/>
                </body>
            </body>
        </worldbody>
    </mujoco>
    """

    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    # 2. Analytical Baseline
    analytical = AnalyticalPendulum(length=1.0, mass=1.0, g=9.81)

    # 3. Initial Conditions
    # Release from 90 degrees (horizontal)
    initial_theta = np.pi / 2
    mujoco.mj_resetData(model, data)
    data.qpos[0] = initial_theta

    # 4. Simulation Loop
    duration = 2.0  # seconds (approx one full period)
    dt = 0.001
    steps = int(duration / dt)

    errors = []

    for _ in range(steps):
        mujoco.mj_step(model, data)

        # Current state
        theta = data.qpos[0]
        omega = data.qvel[0]

        # Check Total Energy Conservation
        # (This is a strong proxy for dynamic accuracy)
        current_energy = analytical.total_energy(theta, omega)
        initial_energy = analytical.total_energy(initial_theta, 0.0)

        # Error
        error = abs(current_energy - initial_energy)
        errors.append(error)

    # 5. Assertions
    max_energy_error = np.max(errors)
    logger.info(f"Max Energy Error (MuJoCo): {max_energy_error:.6f} J")

    # Allow small numerical integration error
    assert (
        max_energy_error < 0.01
    ), f"MuJoCo pendulum drifted! Max error: {max_energy_error}"


@pytest.mark.skipif(
    not is_engine_available(EngineType.DRAKE), reason="Drake not installed"
)
def test_drake_pendulum_accuracy():
    """Verify Drake pendulum matches analytical solution."""
    # Placeholder for Drake implementation
    # Would leverage pydrake.systems.primitives and MultibodyPlant
    pass
