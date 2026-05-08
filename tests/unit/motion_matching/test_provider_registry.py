"""Unit tests for the motion-matching provider registry (issue #4514)."""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.motion_matching.fit_swing import (
    FitMetrics,
    FitOptions,
    FitResult,
    FitTarget,
)
from src.shared.python.motion_matching.provider_registry import (
    available_engines,
    get_provider,
    register_provider,
    unregister_provider,
)

pytestmark = pytest.mark.unit


def _make_target(n: int = 4) -> FitTarget:
    from src.shared.python.motion_matching.club_target import (
        ClubTarget,
        SourceProvenance,
    )

    time = np.linspace(0.0, 0.3, n)
    butt = np.zeros((n, 3))
    clubhead = np.zeros((n, 3))
    clubhead[:, 2] = np.linspace(0.0, 0.1, n)
    quat = np.zeros((n, 4))
    quat[:, 0] = 1.0
    return ClubTarget(
        time=time,
        butt=butt,
        clubhead=clubhead,
        club_quat=quat,
        impact_idx=n - 1,
        source=SourceProvenance(
            filename="t.xlsx",
            format="xlsx",
            subject_id="TW",
            trial_id="T1",
            sha256="0" * 64,
        ),
    )


class _FakeProvider:
    def __init__(self, name: str = "fake") -> None:
        self.engine_name = name
        self.calls = 0

    def fit_swing(self, target: FitTarget, opts: FitOptions) -> FitResult:
        del opts
        self.calls += 1
        n = target.time.shape[0]
        return FitResult(
            theta=np.zeros((n, 2), dtype=np.float64),
            target=target,
            simulated_clubhead=np.zeros((n, 3), dtype=np.float64),
            simulated_butt=np.zeros((n, 3), dtype=np.float64),
            cost_breakdown={},
            metrics=FitMetrics(
                rmse_clubhead=0.0,
                max_clubhead_error_m=0.0,
                time_of_impact_error_s=0.0,
                convergence_norm=0.0,
            ),
            engine_name=self.engine_name,
            engine_version="0.0.1",
            wall_time_s=0.0,
            n_iters=1,
            converged=True,
        )

    def supports_body_target(self) -> bool:
        return False

    def supports_ball_target(self) -> bool:
        return False


@pytest.fixture(autouse=True)
def _isolate_registry() -> None:
    """Clean up any registered providers used by these tests."""
    for name in ("fake", "alpha", "beta"):
        unregister_provider(name)
    yield
    for name in ("fake", "alpha", "beta"):
        unregister_provider(name)


class TestProviderRegistry:
    def test_round_trip(self) -> None:
        provider = _FakeProvider("fake")
        register_provider(provider)
        retrieved = get_provider("fake")
        assert retrieved is provider
        result = retrieved.fit_swing(_make_target(), FitOptions())
        assert isinstance(result, FitResult)
        assert provider.calls == 1

    def test_idempotent_registration(self) -> None:
        p1 = _FakeProvider("fake")
        p2 = _FakeProvider("fake")
        register_provider(p1)
        register_provider(p2)  # no-op
        assert get_provider("fake") is p1

    def test_available_engines_lists_registered(self) -> None:
        register_provider(_FakeProvider("alpha"))
        register_provider(_FakeProvider("beta"))
        engines = available_engines()
        assert "alpha" in engines
        assert "beta" in engines
        # Sorted invariant.
        assert engines == sorted(engines)

    def test_get_unknown_raises_keyerror_with_available(self) -> None:
        register_provider(_FakeProvider("alpha"))
        with pytest.raises(KeyError) as ei:
            get_provider("nonexistent")
        msg = str(ei.value)
        assert "nonexistent" in msg
        assert "alpha" in msg

    def test_unregister_cleans_up(self) -> None:
        register_provider(_FakeProvider("fake"))
        assert "fake" in available_engines()
        unregister_provider("fake")
        assert "fake" not in available_engines()
        unregister_provider("fake")  # no-op second time

    def test_register_rejects_non_provider(self) -> None:
        with pytest.raises(TypeError):
            register_provider("not-a-provider")  # type: ignore[arg-type]

    def test_register_rejects_empty_name(self) -> None:
        class _Empty:
            engine_name = ""

            def fit_swing(self, target: FitTarget, opts: FitOptions) -> FitResult:
                raise NotImplementedError

            def supports_body_target(self) -> bool:
                return False

            def supports_ball_target(self) -> bool:
                return False

        with pytest.raises(ValueError, match="engine_name"):
            register_provider(_Empty())
