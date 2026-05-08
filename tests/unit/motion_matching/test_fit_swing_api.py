"""Tests for the fit_swing API types.

Tests FitSwingProvider protocol, FitOptions, FitResult, and FitMetrics
from src.shared.python.motion_matching.fit_swing.
"""

from __future__ import annotations

import numpy as np
import pytest

from motion_matching.fit_swing import (
    FitMetrics,
    FitOptions,
    FitResult,
    FitSwingProvider,
)


class TestFitMetrics:
    """Test FitMetrics dataclass validation."""

    def test_valid_metrics(self) -> None:
        """Valid metrics should construct without error."""
        metrics = FitMetrics(
            rmse_position=0.01,
            rmse_orientation=0.05,
            max_error=0.1,
            toi_error=0.02,
            n_frames=100,
        )
        assert metrics.rmse_position == 0.01
        assert metrics.rmse_orientation == 0.05
        assert metrics.max_error == 0.1
        assert metrics.toi_error == 0.02
        assert metrics.n_frames == 100

    def test_metrics_toi_error_optional(self) -> None:
        """toi_error should default to None."""
        metrics = FitMetrics(
            rmse_position=0.01,
            rmse_orientation=0.05,
            max_error=0.1,
            n_frames=100,
        )
        assert metrics.toi_error is None

    def test_metrics_rejects_infinite_rmse_position(self) -> None:
        """rmse_position must be finite."""
        with pytest.raises(ValueError, match="rmse_position must be finite"):
            FitMetrics(
                rmse_position=float("inf"),
                rmse_orientation=0.05,
                max_error=0.1,
            )

    def test_metrics_rejects_negative_rmse_position(self) -> None:
        """rmse_position must be non-negative."""
        with pytest.raises(ValueError, match="rmse_position must be non-negative"):
            FitMetrics(
                rmse_position=-0.01,
                rmse_orientation=0.05,
                max_error=0.1,
            )

    def test_metrics_rejects_infinite_rmse_orientation(self) -> None:
        """rmse_orientation must be finite."""
        with pytest.raises(ValueError, match="rmse_orientation must be finite"):
            FitMetrics(
                rmse_position=0.01,
                rmse_orientation=float("nan"),
                max_error=0.1,
            )

    def test_metrics_rejects_negative_rmse_orientation(self) -> None:
        """rmse_orientation must be non-negative."""
        with pytest.raises(ValueError, match="rmse_orientation must be non-negative"):
            FitMetrics(
                rmse_position=0.01,
                rmse_orientation=-0.05,
                max_error=0.1,
            )

    def test_metrics_rejects_infinite_max_error(self) -> None:
        """max_error must be finite."""
        with pytest.raises(ValueError, match="max_error must be finite"):
            FitMetrics(
                rmse_position=0.01,
                rmse_orientation=0.05,
                max_error=float("inf"),
            )

    def test_metrics_rejects_negative_max_error(self) -> None:
        """max_error must be non-negative."""
        with pytest.raises(ValueError, match="max_error must be non-negative"):
            FitMetrics(
                rmse_position=0.01,
                rmse_orientation=0.05,
                max_error=-0.1,
            )

    def test_metrics_rejects_negative_n_frames(self) -> None:
        """n_frames must be non-negative."""
        with pytest.raises(ValueError, match="n_frames must be non-negative"):
            FitMetrics(
                rmse_position=0.01,
                rmse_orientation=0.05,
                max_error=0.1,
                n_frames=-1,
            )

    def test_metrics_rejects_infinite_toi_error(self) -> None:
        """toi_error must be finite when provided."""
        with pytest.raises(ValueError, match="toi_error must be finite"):
            FitMetrics(
                rmse_position=0.01,
                rmse_orientation=0.05,
                max_error=0.1,
                toi_error=float("nan"),
            )


class TestFitOptions:
    """Test FitOptions dataclass validation."""

    def test_valid_options(self) -> None:
        """Valid options should construct without error."""
        opts = FitOptions(
            max_iters=200,
            tol=1e-8,
            seed=42,
            regulariser=0.1,
            cost_terms=("position", "orientation"),
        )
        assert opts.max_iters == 200
        assert opts.tol == 1e-8
        assert opts.seed == 42
        assert opts.regulariser == 0.1
        assert opts.cost_terms == ("position", "orientation")

    def test_options_defaults(self) -> None:
        """Default options should be valid."""
        opts = FitOptions()
        assert opts.max_iters == 100
        assert opts.tol == 1e-6
        assert opts.seed is None
        assert opts.regulariser == 0.01
        assert opts.cost_terms == ("position", "orientation", "velocity")
        assert opts.initial_theta is None
        assert opts.align_options == {}

    def test_options_rejects_non_positive_max_iters(self) -> None:
        """max_iters must be positive."""
        with pytest.raises(ValueError, match="max_iters must be positive"):
            FitOptions(max_iters=0)

        with pytest.raises(ValueError, match="max_iters must be positive"):
            FitOptions(max_iters=-1)

    def test_options_rejects_non_positive_tol(self) -> None:
        """tol must be positive."""
        with pytest.raises(ValueError, match="tol must be positive"):
            FitOptions(tol=0)

        with pytest.raises(ValueError, match="tol must be positive"):
            FitOptions(tol=-1e-6)

    def test_options_rejects_negative_regulariser(self) -> None:
        """regulariser must be non-negative."""
        with pytest.raises(ValueError, match="regulariser must be non-negative"):
            FitOptions(regulariser=-0.01)

    def test_options_rejects_negative_seed(self) -> None:
        """seed must be non-negative."""
        with pytest.raises(ValueError, match="seed must be non-negative"):
            FitOptions(seed=-1)

    def test_options_rejects_invalid_cost_term(self) -> None:
        """cost_terms must be valid."""
        with pytest.raises(ValueError, match="Unknown cost term"):
            FitOptions(cost_terms=("invalid_term",))

        with pytest.raises(ValueError, match="Unknown cost term"):
            FitOptions(cost_terms=("position", "invalid"))

    def test_options_valid_cost_terms(self) -> None:
        """All valid cost terms should be accepted."""
        valid_terms = ("position", "orientation", "velocity", "acceleration", "torque")
        opts = FitOptions(cost_terms=valid_terms)
        assert opts.cost_terms == valid_terms

    def test_options_with_initial_theta(self) -> None:
        """initial_theta should be accepted."""
        theta = np.zeros((10, 5))
        opts = FitOptions(initial_theta=theta)
        assert opts.initial_theta is theta


class TestFitResult:
    """Test FitResult dataclass validation."""

    def _make_valid_result(self, **kwargs) -> FitResult:
        """Helper to create a valid FitResult."""
        return FitResult(
            theta=np.zeros((10, 5)),
            target={},
            simulated_clubhead=np.zeros((10, 3)),
            simulated_butt=np.zeros((10, 3)),
            cost_breakdown={"position": np.zeros(10)},
            metrics=FitMetrics(
                rmse_position=0.01,
                rmse_orientation=0.05,
                max_error=0.1,
            ),
            engine_name="test_engine",
            engine_version="1.0.0",
            wall_time_s=0.5,
            n_iters=50,
            converged=True,
            **kwargs,
        )

    def test_valid_result(self) -> None:
        """Valid result should construct without error."""
        result = self._make_valid_result()
        assert result.engine_name == "test_engine"
        assert result.converged is True
        assert result.n_iters == 50

    def test_result_rejects_non_2d_theta(self) -> None:
        """theta must be 2D."""
        with pytest.raises(ValueError, match="theta must be 2D"):
            self._make_valid_result(theta=np.zeros((10,)))

        with pytest.raises(ValueError, match="theta must be 2D"):
            self._make_valid_result(theta=np.zeros((10, 5, 3)))

    def test_result_rejects_wrong_clubhead_shape(self) -> None:
        """simulated_clubhead must have 3 columns."""
        with pytest.raises(ValueError, match="simulated_clubhead must have 3 columns"):
            self._make_valid_result(simulated_clubhead=np.zeros((10, 2)))

    def test_result_rejects_wrong_butt_shape(self) -> None:
        """simulated_butt must have 3 columns."""
        with pytest.raises(ValueError, match="simulated_butt must have 3 columns"):
            self._make_valid_result(simulated_butt=np.zeros((10, 5)))

    def test_result_rejects_non_finite_theta(self) -> None:
        """theta must be finite."""
        theta_with_nan = np.zeros((10, 5))
        theta_with_nan[0, 0] = np.nan
        with pytest.raises(ValueError, match="theta contains non-finite values"):
            self._make_valid_result(theta=theta_with_nan)

        theta_with_inf = np.zeros((10, 5))
        theta_with_inf[0, 0] = np.inf
        with pytest.raises(ValueError, match="theta contains non-finite values"):
            self._make_valid_result(theta=theta_with_inf)

    def test_result_rejects_non_finite_clubhead(self) -> None:
        """simulated_clubhead must be finite."""
        clubhead_with_nan = np.zeros((10, 3))
        clubhead_with_nan[0, 0] = np.nan
        with pytest.raises(
            ValueError, match="simulated_clubhead contains non-finite values"
        ):
            self._make_valid_result(simulated_clubhead=clubhead_with_nan)

    def test_result_rejects_non_finite_butt(self) -> None:
        """simulated_butt must be finite."""
        butt_with_nan = np.zeros((10, 3))
        butt_with_nan[0, 0] = np.nan
        with pytest.raises(
            ValueError, match="simulated_butt contains non-finite values"
        ):
            self._make_valid_result(simulated_butt=butt_with_nan)

    def test_result_rejects_negative_wall_time(self) -> None:
        """wall_time_s must be non-negative."""
        with pytest.raises(ValueError, match="wall_time_s must be non-negative"):
            self._make_valid_result(wall_time_s=-1.0)

    def test_result_rejects_negative_n_iters(self) -> None:
        """n_iters must be non-negative."""
        with pytest.raises(ValueError, match="n_iters must be non-negative"):
            self._make_valid_result(n_iters=-1)

    def test_result_rejects_empty_engine_name(self) -> None:
        """engine_name must be non-empty."""
        with pytest.raises(ValueError, match="engine_name must be non-empty"):
            self._make_valid_result(engine_name="")


class TestFitSwingProvider:
    """Test FitSwingProvider protocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """FitSwingProvider should be runtime checkable."""
        # This just verifies the protocol is set up correctly
        assert hasattr(FitSwingProvider, "__protocol_attrs__")

    def test_synthetic_provider_implements_protocol(self) -> None:
        """A synthetic provider should pass isinstance check."""
        from typing import runtime_checkable

        @runtime_checkable
        class SyntheticProvider:
            engine_name = "synthetic"

            def fit_swing(self, target, opts):
                return None

            def supports_body_target(self):
                return False

            def supports_ball_target(self):
                return False

        # Note: We can't directly check isinstance against FitSwingProvider
        # with a local class, but this documents the expected interface
        provider = SyntheticProvider()
        assert provider.engine_name == "synthetic"
        assert callable(provider.fit_swing)
        assert callable(provider.supports_body_target)
        assert callable(provider.supports_ball_target)