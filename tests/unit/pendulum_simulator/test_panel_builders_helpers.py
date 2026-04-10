"""Tests for pendulum GUI panel builder helpers."""

from __future__ import annotations

import math
import sys
from types import ModuleType

import numpy as np
import pytest

pytest.importorskip("PyQt6")


def _install_fake_simulation_modules() -> None:
    class _FakeResultBase:
        pass

    for module_name in (
        "src.shared.python.pendulum_simulator.simulation",
        "src.shared.python.pendulum_simulator.simulation_triple",
        "src.shared.python.pendulum_simulator.simulation_golfer",
    ):
        module = ModuleType(module_name)
        module.make_polynomial_torque = lambda *args, **kwargs: (args, kwargs)
        module.run_simulation = lambda *args, **kwargs: kwargs
        if module_name.endswith(".simulation"):
            module.SimulationResult = _FakeResultBase
        elif module_name.endswith(".simulation_triple"):
            module.TripleSimulationResult = _FakeResultBase
        else:
            module.GolferSimulationResult = _FakeResultBase
        sys.modules[module_name] = module


def _install_fake_perturbation_modules() -> None:
    package = ModuleType("src.shared.python.pendulum_simulator.perturbation")
    package.__path__ = []  # type: ignore[attr-defined]
    sys.modules["src.shared.python.pendulum_simulator.perturbation"] = package

    config_module = ModuleType(
        "src.shared.python.pendulum_simulator.perturbation.config"
    )

    class _FakePerturbationConfig:
        pass

    class _FakePerturbationSummary:
        pass

    config_module.PerturbationConfig = _FakePerturbationConfig  # type: ignore[attr-defined]
    config_module.PerturbationSummary = _FakePerturbationSummary  # type: ignore[attr-defined]
    sys.modules["src.shared.python.pendulum_simulator.perturbation.config"] = (
        config_module
    )

    analyzer_module = ModuleType(
        "src.shared.python.pendulum_simulator.pendulum_perturbation_analyzer"
    )

    class _FakePendulumPerturbationAnalyzer:
        pass

    analyzer_module.PendulumPerturbationAnalyzer = _FakePendulumPerturbationAnalyzer  # type: ignore[attr-defined]
    sys.modules[
        "src.shared.python.pendulum_simulator.pendulum_perturbation_analyzer"
    ] = analyzer_module

    perturbation_analysis_module = ModuleType(
        "src.shared.python.pendulum_simulator.perturbation_analysis"
    )
    perturbation_analysis_module.variability_summary = lambda *args, **kwargs: None

    sys.modules["src.shared.python.pendulum_simulator.perturbation_analysis"] = (
        perturbation_analysis_module
    )


_install_fake_simulation_modules()
_install_fake_perturbation_modules()

from src.shared.python.pendulum_simulator.gui import panel_builders  # noqa: E402


class _FakeResult:
    def __init__(self, positions, velocities, times) -> None:
        self._positions = positions
        self._velocities = velocities
        self.t = np.asarray(times)
        self.n_steps = len(times)

    def positions_at(self, idx: int):
        return self._positions[idx]

    def velocities_at(self, idx: int):
        return self._velocities[idx]

    def to_df(self):
        import pandas as pd

        df = pd.DataFrame(
            {
                "time": self.t,
            }
        )
        for i in range(len(self._positions[0])):
            df[f"angle_{i + 1}"] = [p[i] for p in self._positions]
            df[f"velocity_{i + 1}"] = [v[i] for v in self._velocities]
        return df


class _FakeConfig:
    pass


class TestPanelBuildersHelpers:
    def old_test_create_velocity_plot_data(self) -> None:
        times = [0.0, 0.1, 0.2]
        positions = [[0.1, 0.2], [0.15, 0.25], [0.2, 0.3]]
        velocities = [[1.0, 2.0], [1.1, 2.1], [1.2, 2.2]]
        result = _FakeResult(positions, velocities, times)

        x, y1, y2 = panel_builders._create_velocity_plot_data(result, 2)

        assert np.array_equal(x, times)
        assert np.array_equal(y1, [1.0, 1.1, 1.2])
        assert np.array_equal(y2, [2.0, 2.1, 2.2])

    def old_test_create_phase_plot_data(self) -> None:
        times = [0.0, 0.1, 0.2]
        positions = [[0.1, 0.2], [0.15, 0.25], [0.2, 0.3]]
        velocities = [[1.0, 2.0], [1.1, 2.1], [1.2, 2.2]]
        result = _FakeResult(positions, velocities, times)

        x, y1, y2 = panel_builders._create_phase_plot_data(result, 2)

        assert np.array_equal(x, [0.1, 0.15, 0.2])
        assert np.array_equal(y1, [1.0, 1.1, 1.2])
        assert np.array_equal(y2, [2.0, 2.1, 2.2])

    def old_test_create_energy_plot_data_double(self) -> None:
        times = [0.0, 0.1, 0.2]
        positions = [[0.1, 0.2], [0.15, 0.25], [0.2, 0.3]]
        velocities = [[1.0, 2.0], [1.1, 2.1], [1.2, 2.2]]
        result = _FakeResult(positions, velocities, times)
        config = _FakeConfig()
        config.m1 = 1.0  # type: ignore[attr-defined]
        config.m2 = 1.0  # type: ignore[attr-defined]
        config.l1 = 1.0  # type: ignore[attr-defined]
        config.l2 = 1.0  # type: ignore[attr-defined]
        config.g = 9.81  # type: ignore[attr-defined]

        x, e_kin, e_pot, e_tot = panel_builders._create_energy_plot_data_double(
            result, config
        )

        assert np.array_equal(x, times)
        assert len(e_kin) == 3
        assert len(e_pot) == 3
        assert len(e_tot) == 3

        # Simple bounds check, actual math is in energy_components which we assume is correct
        assert all(e > 0 for e in e_kin)
        assert all(math.isfinite(e) for e in e_pot)
        assert all(math.isfinite(e) for e in e_tot)
        assert np.allclose(e_tot, np.array(e_kin) + np.array(e_pot))
