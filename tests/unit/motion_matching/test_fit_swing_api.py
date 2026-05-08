"""Unit tests for the canonical ``fit_swing`` API (issue #4514)."""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.motion_matching.fit_swing import (
    CostTerm,
    FitMetrics,
    FitOptions,
    FitResult,
    FitSwingProvider,
    FitTarget,
)
from src.shared.python.motion_matching.target import AlignOptions

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _good_metrics() -> FitMetrics:
    return FitMetrics(
        rmse_clubhead=0.01,
        max_clubhead_error_m=0.05,
        time_of_impact_error_s=-0.001,
        convergence_norm=1e-7,
    )


def _good_fit_result(n: int = 4, n_joints: int = 3) -> FitResult:
    theta = np.zeros((n, n_joints), dtype=np.float64)
    sim_clubhead = np.zeros((n, 3), dtype=np.float64)
    sim_butt = np.zeros((n, 3), dtype=np.float64)
    cost = {"clubhead_position": np.zeros(n, dtype=np.float64)}

    target = _make_club_target(n)

    return FitResult(
        theta=theta,
        target=target,
        simulated_clubhead=sim_clubhead,
        simulated_butt=sim_butt,
        cost_breakdown=cost,
        metrics=_good_metrics(),
        engine_name="synthetic",
        engine_version="0.0.0",
        wall_time_s=0.5,
        n_iters=10,
        converged=True,
    )


def _make_club_target(n: int) -> FitTarget:
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


# ---------------------------------------------------------------------------
# FitOptions
# ---------------------------------------------------------------------------


class TestFitOptions:
    def test_defaults_construct(self) -> None:
        opts = FitOptions()
        assert opts.max_iters == 100
        assert opts.regulariser == "l2"
        assert CostTerm.CLUBHEAD_POSITION in opts.cost_terms
        assert isinstance(opts.align, AlignOptions)

    def test_align_must_be_align_options(self) -> None:
        with pytest.raises(TypeError, match="align"):
            FitOptions(align="impact")  # type: ignore[arg-type]

    def test_max_iters_positive(self) -> None:
        with pytest.raises(ValueError, match="max_iters"):
            FitOptions(max_iters=0)
        with pytest.raises(ValueError, match="max_iters"):
            FitOptions(max_iters=-1)

    def test_tol_finite_nonneg(self) -> None:
        with pytest.raises(ValueError, match="tol"):
            FitOptions(tol=-1.0)
        with pytest.raises(ValueError, match="tol"):
            FitOptions(tol=float("nan"))

    def test_seed_validation(self) -> None:
        FitOptions(seed=None)
        FitOptions(seed=0)
        with pytest.raises(ValueError, match="seed"):
            FitOptions(seed=-1)

    def test_regulariser_nonempty(self) -> None:
        with pytest.raises(ValueError, match="regulariser"):
            FitOptions(regulariser="")

    def test_cost_terms_must_be_frozenset(self) -> None:
        with pytest.raises(TypeError, match="cost_terms"):
            FitOptions(cost_terms={CostTerm.EFFORT})  # type: ignore[arg-type]

    def test_cost_terms_nonempty(self) -> None:
        with pytest.raises(ValueError, match="cost_terms"):
            FitOptions(cost_terms=frozenset())

    def test_cost_terms_entries_must_be_enum(self) -> None:
        with pytest.raises(TypeError, match="CostTerm"):
            FitOptions(cost_terms=frozenset({"clubhead"}))  # type: ignore[arg-type]

    def test_initial_theta_shape(self) -> None:
        FitOptions(initial_theta=np.zeros(5))
        FitOptions(initial_theta=np.zeros((4, 3)))
        with pytest.raises(ValueError, match="initial_theta"):
            FitOptions(initial_theta=np.zeros((2, 2, 2)))
        with pytest.raises(ValueError, match="NaN"):
            FitOptions(initial_theta=np.array([np.nan, 0.0]))


# ---------------------------------------------------------------------------
# FitMetrics
# ---------------------------------------------------------------------------


class TestFitMetrics:
    def test_happy(self) -> None:
        m = _good_metrics()
        assert m.rmse_clubhead == 0.01

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValueError, match="rmse_clubhead"):
            FitMetrics(
                rmse_clubhead=float("nan"),
                max_clubhead_error_m=0.0,
                time_of_impact_error_s=0.0,
                convergence_norm=0.0,
            )

    def test_rejects_negative_rmse(self) -> None:
        with pytest.raises(ValueError, match="rmse_clubhead"):
            FitMetrics(
                rmse_clubhead=-0.01,
                max_clubhead_error_m=0.0,
                time_of_impact_error_s=0.0,
                convergence_norm=0.0,
            )

    def test_negative_toi_allowed(self) -> None:
        # Time-of-impact error is signed.
        m = FitMetrics(
            rmse_clubhead=0.0,
            max_clubhead_error_m=0.0,
            time_of_impact_error_s=-0.005,
            convergence_norm=0.0,
        )
        assert m.time_of_impact_error_s < 0

    def test_negative_convergence_rejected(self) -> None:
        with pytest.raises(ValueError, match="convergence_norm"):
            FitMetrics(
                rmse_clubhead=0.0,
                max_clubhead_error_m=0.0,
                time_of_impact_error_s=0.0,
                convergence_norm=-1.0,
            )


# ---------------------------------------------------------------------------
# FitResult
# ---------------------------------------------------------------------------


class TestFitResult:
    def test_happy(self) -> None:
        r = _good_fit_result()
        assert r.theta.shape == (4, 3)
        assert r.engine_name == "synthetic"

    def test_theta_must_be_2d(self) -> None:
        target = _make_club_target(4)
        with pytest.raises(ValueError, match="theta"):
            FitResult(
                theta=np.zeros(4),
                target=target,
                simulated_clubhead=np.zeros((4, 3)),
                simulated_butt=np.zeros((4, 3)),
                cost_breakdown={},
                metrics=_good_metrics(),
                engine_name="x",
                engine_version="1",
                wall_time_s=0.0,
                n_iters=0,
                converged=False,
            )

    def test_simulated_shape_must_match(self) -> None:
        target = _make_club_target(4)
        with pytest.raises(ValueError, match="simulated_clubhead"):
            FitResult(
                theta=np.zeros((4, 3)),
                target=target,
                simulated_clubhead=np.zeros((3, 3)),
                simulated_butt=np.zeros((4, 3)),
                cost_breakdown={},
                metrics=_good_metrics(),
                engine_name="x",
                engine_version="1",
                wall_time_s=0.0,
                n_iters=0,
                converged=False,
            )

    def test_cost_breakdown_value_must_be_array_of_n(self) -> None:
        target = _make_club_target(4)
        with pytest.raises(ValueError, match="cost_breakdown"):
            FitResult(
                theta=np.zeros((4, 3)),
                target=target,
                simulated_clubhead=np.zeros((4, 3)),
                simulated_butt=np.zeros((4, 3)),
                cost_breakdown={"x": np.zeros(3)},
                metrics=_good_metrics(),
                engine_name="x",
                engine_version="1",
                wall_time_s=0.0,
                n_iters=0,
                converged=False,
            )

    def test_engine_name_nonempty(self) -> None:
        target = _make_club_target(4)
        with pytest.raises(ValueError, match="engine_name"):
            FitResult(
                theta=np.zeros((4, 3)),
                target=target,
                simulated_clubhead=np.zeros((4, 3)),
                simulated_butt=np.zeros((4, 3)),
                cost_breakdown={},
                metrics=_good_metrics(),
                engine_name="",
                engine_version="1",
                wall_time_s=0.0,
                n_iters=0,
                converged=False,
            )

    def test_wall_time_nonneg(self) -> None:
        target = _make_club_target(4)
        with pytest.raises(ValueError, match="wall_time_s"):
            FitResult(
                theta=np.zeros((4, 3)),
                target=target,
                simulated_clubhead=np.zeros((4, 3)),
                simulated_butt=np.zeros((4, 3)),
                cost_breakdown={},
                metrics=_good_metrics(),
                engine_name="x",
                engine_version="1",
                wall_time_s=-0.1,
                n_iters=0,
                converged=False,
            )

    def test_nan_rejected(self) -> None:
        target = _make_club_target(4)
        bad = np.zeros((4, 3))
        bad[0, 0] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            FitResult(
                theta=bad,
                target=target,
                simulated_clubhead=np.zeros((4, 3)),
                simulated_butt=np.zeros((4, 3)),
                cost_breakdown={},
                metrics=_good_metrics(),
                engine_name="x",
                engine_version="1",
                wall_time_s=0.0,
                n_iters=0,
                converged=False,
            )


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class _SyntheticProvider:
    """Test fixture provider satisfying :class:`FitSwingProvider`."""

    engine_name: str = "synthetic"

    def fit_swing(self, target: FitTarget, opts: FitOptions) -> FitResult:
        del opts
        n = target.time.shape[0] if hasattr(target, "time") else 4
        return _good_fit_result(n=n, n_joints=3)

    def supports_body_target(self) -> bool:
        return False

    def supports_ball_target(self) -> bool:
        return False


class TestFitSwingProvider:
    def test_runtime_checkable_isinstance(self) -> None:
        provider = _SyntheticProvider()
        assert isinstance(provider, FitSwingProvider)

    def test_synthetic_round_trip(self) -> None:
        provider = _SyntheticProvider()
        target = _make_club_target(6)
        result = provider.fit_swing(target, FitOptions())
        assert isinstance(result, FitResult)
        assert result.theta.shape[0] == 6

    def test_non_provider_not_isinstance(self) -> None:
        class _Bad:
            pass

        assert not isinstance(_Bad(), FitSwingProvider)
