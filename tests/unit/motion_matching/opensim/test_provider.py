"""Unit tests for ``OpenSimFitSwingProvider`` (issue #4518).

These tests verify that the OpenSim adapter satisfies the canonical
:class:`FitSwingProvider` contract introduced by issue #4514.

The full prescribed-controller path needs the ``opensim`` wheel; tests are
skipped when it is not importable. The provider, however, must register
itself at module-import time even in slim environments, so the registration
test does not require ``opensim``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.shared.python.motion_matching.club_target import (
    ClubTarget,
    SourceProvenance,
)
from src.shared.python.motion_matching.cost import SimOutput
from src.shared.python.motion_matching.fit_swing import (
    CostTerm,
    FitOptions,
)
from src.shared.python.motion_matching.fit_swing import (
    FitResult as FitSwingResult,
)
from src.shared.python.motion_matching.provider_registry import (
    available_engines,
    get_provider,
    unregister_provider,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_synthetic_target(n: int = 51) -> ClubTarget:
    """Small but valid ClubTarget for unit tests."""
    time = np.linspace(0.0, 0.3, n)
    butt = np.column_stack(
        [
            0.4 * np.sin(2.0 * np.pi * time),
            0.4 * np.cos(2.0 * np.pi * time),
            np.zeros_like(time),
        ]
    )
    clubhead = butt + np.array([0.0, 0.0, 1.0])
    quat = np.tile(np.array([1.0, 0.0, 0.0, 0.0]), (n, 1))
    return ClubTarget(
        time=time,
        butt=butt,
        clubhead=clubhead,
        club_quat=quat,
        impact_idx=n - 1,
        source=SourceProvenance(
            filename="synthetic.bin",
            format="synthetic",
            subject_id="UT",
            trial_id="0",
            sha256="0" * 64,
        ),
    )


def _make_kinematic_simulate_fn(target: ClubTarget):
    """Deterministic mock simulator: returns a slightly-perturbed copy of target.

    The mock is independent of the polynomial coefficients ``theta`` so the
    SLSQP driver converges in 1-2 iterations. This keeps the unit test fast
    while exercising the full I/O conversion in
    :class:`OpenSimFitSwingProvider`.
    """

    def simulate(theta: np.ndarray) -> SimOutput:
        # Tiny theta-dependent perturbation so the cost is non-degenerate.
        scale = 1e-4 * float(np.tanh(np.linalg.norm(theta) / 100.0))
        return SimOutput(
            butt=target.butt + scale,
            clubhead=target.clubhead + scale,
            club_quat=target.club_quat,
            time=target.time.copy(),
            tau=np.zeros((target.time.size, 25)),
            omega=np.zeros((target.time.size, 25)),
        )

    simulate.n_joints = 25  # type: ignore[attr-defined]
    return simulate


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    """The provider must register itself when its package is imported."""

    def test_registered_at_import(self) -> None:
        # Importing the package triggers ``register_provider``.
        import src.engines.physics_engines.opensim.python.motion_matching  # noqa: F401

        assert "opensim" in available_engines()

    def test_get_provider_round_trip(self) -> None:
        import src.engines.physics_engines.opensim.python.motion_matching  # noqa: F401

        provider = get_provider("opensim")
        assert provider.engine_name == "opensim"
        assert provider.supports_body_target() is False
        assert provider.supports_ball_target() is False
        # ``engine_version`` is populated at construction.
        assert isinstance(provider.engine_version, str)
        assert provider.engine_version  # non-empty


# ---------------------------------------------------------------------------
# fit_swing end-to-end (mock simulator: no opensim wheel required)
# ---------------------------------------------------------------------------


class TestFitSwingMock:
    """End-to-end fit_swing with an injected kinematic mock simulator.

    The mock means we exercise the full I/O conversion (FitOptions ->
    OpenSim FitOptions, FitResult -> FitSwingResult) without paying for the
    real OpenSim integration.
    """

    def test_returns_valid_fit_swing_result(self) -> None:
        from src.engines.physics_engines.opensim.python.motion_matching.provider import (
            OpenSimFitSwingProvider,
        )

        target = _make_synthetic_target()
        sim_fn = _make_kinematic_simulate_fn(target)
        provider = OpenSimFitSwingProvider(simulate_fn=sim_fn)

        opts = FitOptions(
            max_iters=2,
            tol=1e-3,
            seed=42,
            cost_terms=frozenset({CostTerm.CLUBHEAD_POSITION}),
        )
        result = provider.fit_swing(target, opts)

        assert isinstance(result, FitSwingResult)
        n_frames = target.time.size
        assert result.theta.shape == (n_frames, 25 * 7)
        assert result.simulated_clubhead.shape == (n_frames, 3)
        assert result.simulated_butt.shape == (n_frames, 3)
        assert "clubhead_position" in result.cost_breakdown
        assert result.engine_name == "opensim"
        assert np.isfinite(result.metrics.rmse_clubhead)
        assert result.metrics.rmse_clubhead >= 0.0
        assert np.isfinite(result.metrics.max_clubhead_error_m)
        assert result.metrics.max_clubhead_error_m >= 0.0
        assert result.wall_time_s >= 0.0
        assert result.n_iters >= 0

    def test_rejects_non_club_target(self) -> None:
        from src.engines.physics_engines.opensim.python.motion_matching.provider import (
            OpenSimFitSwingProvider,
        )

        provider = OpenSimFitSwingProvider(simulate_fn=lambda t: None)  # type: ignore[arg-type, return-value]
        with pytest.raises(TypeError, match="ClubTarget"):
            provider.fit_swing("not a target", FitOptions())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Numerical regression: clubhead speed at impact
# ---------------------------------------------------------------------------


_LEADERBOARD_PATH = (
    Path(__file__).resolve().parents[4] / "reports" / "cross_engine_leaderboard.json"
)

# Pinned clubhead-speed-at-impact for the synthetic target above, computed
# from the kinematic mock at first run. The 1% tolerance is asserted below.
# This pin protects against silent drift in the I/O conversion path.
_PINNED_CLUBHEAD_SPEED_AT_IMPACT_MPS = 2.51327


def _expected_clubhead_speed_mps() -> float:
    """Read the leaderboard pin if it exists, else fall back to literal."""
    if _LEADERBOARD_PATH.exists():
        try:
            data = json.loads(_LEADERBOARD_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return _PINNED_CLUBHEAD_SPEED_AT_IMPACT_MPS
        for row in data if isinstance(data, list) else data.get("rows", []):
            if (
                isinstance(row, dict)
                and row.get("engine") == "opensim"
                and "clubhead_speed_at_impact_mps" in row
            ):
                return float(row["clubhead_speed_at_impact_mps"])
    return _PINNED_CLUBHEAD_SPEED_AT_IMPACT_MPS


class TestNumericalRegression:
    """Pinned clubhead-speed-at-impact within 1% of leaderboard entry."""

    def test_clubhead_speed_at_impact(self) -> None:
        from src.engines.physics_engines.opensim.python.motion_matching.provider import (
            OpenSimFitSwingProvider,
        )

        target = _make_synthetic_target()
        sim_fn = _make_kinematic_simulate_fn(target)
        provider = OpenSimFitSwingProvider(simulate_fn=sim_fn)
        result = provider.fit_swing(target, FitOptions(max_iters=2))

        ch = result.simulated_clubhead
        # Forward-difference speed at impact - 1 (last interior frame).
        idx = min(target.impact_idx, ch.shape[0] - 1)
        if idx == 0:
            pytest.skip("Need at least 2 frames for a forward difference.")
        dt = float(target.time[idx] - target.time[idx - 1])
        speed = float(np.linalg.norm(ch[idx] - ch[idx - 1]) / max(dt, 1e-9))

        expected = _expected_clubhead_speed_mps()
        rel = abs(speed - expected) / max(expected, 1e-9)
        assert rel < 0.01, (
            f"clubhead speed at impact drifted: got {speed:.5f} m/s, "
            f"expected {expected:.5f} m/s (rel {rel:.2%})"
        )


# ---------------------------------------------------------------------------
# Live OpenSim path (skipped when the wheel is absent)
# ---------------------------------------------------------------------------


class TestLiveOpenSim:
    """Exercises the real OpenSim simulate path. Skipped if wheel not installed."""

    def test_real_opensim_fit_smoke(self) -> None:
        pytest.importorskip("opensim")
        # The real path is exercised by ``test_opensim_simulate_with_coefficients``
        # and the existing prescribed-controller tests. Here we simply confirm
        # the provider can be constructed with the default simulator.
        from src.engines.physics_engines.opensim.python.motion_matching.provider import (
            OpenSimFitSwingProvider,
        )

        provider = OpenSimFitSwingProvider()
        assert provider.engine_name == "opensim"
        # engine_version should be populated when opensim is installed.
        assert provider.engine_version != "unknown"


# ---------------------------------------------------------------------------
# Cleanup: avoid leaking registry state into other tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_registry():
    """Re-register the opensim provider at the end of each test.

    Some tests in this module exercise unregister; we re-import the package
    so the auto-register block runs again.
    """
    yield
    # The package import is cached; re-running register requires a manual
    # re-add via the public API.
    try:
        from src.engines.physics_engines.opensim.python.motion_matching.provider import (
            OpenSimFitSwingProvider,
        )
        from src.shared.python.motion_matching.provider_registry import (
            register_provider,
        )

        if "opensim" not in available_engines():
            register_provider(OpenSimFitSwingProvider())
    except ImportError:
        pass


def _silence_unused_unregister() -> None:
    """Touch ``unregister_provider`` to keep the import alive for future tests."""
    _ = unregister_provider
