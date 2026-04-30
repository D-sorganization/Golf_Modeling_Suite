"""Smoke benchmarks for the performance harness (issue #3510).

These two micro-benchmarks exercise lightweight, deterministic physics
helpers so the pytest-benchmark harness has at least one real workload
to record. They are intentionally cheap (~microseconds each) so they
complete quickly in CI and serve as scaffolding for richer benchmarks
added in follow-up PRs.

Run locally with:

    python3 -m pytest tests/benchmarks -m benchmark --benchmark-only
"""

from __future__ import annotations

import pytest

# pytest-benchmark provides the ``benchmark`` fixture used below. Skip the
# whole module gracefully if it isn't installed (e.g. minimal dev installs).
pytest.importorskip("pytest_benchmark")

# numpy backs the aerodynamics force vectors. If it isn't available there's
# nothing meaningful to benchmark here.
np = pytest.importorskip("numpy")


@pytest.mark.benchmark
def test_drag_model_calculate(benchmark: pytest.fixture) -> None:
    """Benchmark DragModel.calculate on a representative velocity vector."""
    try:
        from src.shared.python.physics.aerodynamics import DragModel
    except ImportError:
        pytest.skip("aerodynamics module not available")

    model = DragModel()
    velocity = np.array([50.0, 0.0, 5.0])
    result = benchmark(model.calculate, velocity)
    assert result.shape == (3,)


@pytest.mark.benchmark
def test_lift_model_calculate(benchmark: pytest.fixture) -> None:
    """Benchmark LiftModel.calculate with backspin around the +Y axis."""
    try:
        from src.shared.python.physics.aerodynamics import LiftModel
    except ImportError:
        pytest.skip("aerodynamics module not available")

    model = LiftModel()
    velocity = np.array([50.0, 0.0, 5.0])
    spin = np.array([0.0, -300.0, 0.0])
    result = benchmark(model.calculate, velocity, spin)
    assert result.shape == (3,)
