"""Canonical engine-side fit_swing API and result types.

Foundation for cross-engine motion matching parity (#4513, #4514).

Defines the FitSwingProvider protocol that each physics engine implements,
along with FitOptions for configuring the optimization and FitResult for
returning standardized results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class FitSwingProvider(Protocol):
    """Engine-side motion-matching entry point.

    Each physics engine (MuJoCo, Drake, Pinocchio, OpenSim, etc.) implements
    this protocol to expose a standardized fit_swing API.

    Attributes:
        engine_name: Canonical engine name identifier.
    """

    engine_name: str

    def fit_swing(
        self,
        target: MultiSourceTarget | ClubTarget | ClubBallTarget,
        opts: FitOptions,
    ) -> FitResult:
        """Fit a swing motion to the given target.

        Args:
            target: The target trajectory to match.
            opts: Optimization options and constraints.

        Returns:
            FitResult with fitted trajectory, metrics, and diagnostics.
        """
        ...

    def supports_body_target(self) -> bool:
        """Check if this engine supports full body target matching."""
        ...

    def supports_ball_target(self) -> bool:
        """Check if this engine supports club ball target matching."""
        ...


@dataclass(frozen=True)
class FitMetrics:
    """Summary metrics from a motion matching fit.

    Attributes:
        rmse_position: Root mean square position error in meters.
        rmse_orientation: Root mean square orientation error in radians.
        max_error: Maximum per-frame error across all terms.
        toi_error: Time-of-impact error (for club-ball collisions).
        n_frames: Number of frames in the fitted trajectory.
    """

    rmse_position: float
    rmse_orientation: float
    max_error: float
    toi_error: float | None = None
    n_frames: int = 0

    def __post_init__(self) -> None:
        """Validate metrics are finite and non-negative."""
        if not np.isfinite(self.rmse_position):
            raise ValueError(f"rmse_position must be finite, got {self.rmse_position}")
        if not np.isfinite(self.rmse_orientation):
            raise ValueError(
                f"rmse_orientation must be finite, got {self.rmse_orientation}"
            )
        if not np.isfinite(self.max_error):
            raise ValueError(f"max_error must be finite, got {self.max_error}")
        if self.rmse_position < 0:
            raise ValueError(f"rmse_position must be non-negative: {self.rmse_position}")
        if self.rmse_orientation < 0:
            raise ValueError(
                f"rmse_orientation must be non-negative: {self.rmse_orientation}"
            )
        if self.max_error < 0:
            raise ValueError(f"max_error must be non-negative: {self.max_error}")
        if self.n_frames < 0:
            raise ValueError(f"n_frames must be non-negative: {self.n_frames}")
        if self.toi_error is not None and not np.isfinite(self.toi_error):
            raise ValueError(f"toi_error must be finite, got {self.toi_error}")


@dataclass(frozen=True)
class FitOptions:
    """Options for configuring motion matching optimization.

    Extends AlignOptions with optimization-specific knobs.

    Attributes:
        max_iters: Maximum optimization iterations.
        tol: Convergence tolerance.
        seed: Random seed for stochastic optimization.
        regulariser: Regularization weight.
        cost_terms: Set of cost terms to include.
        initial_theta: Initial joint angle guess (N, n_joints) or None.
        align_options: Optional alignment options.
    """

    max_iters: int = 100
    tol: float = 1e-6
    seed: int | None = None
    regulariser: float = 0.01
    cost_terms: tuple[str, ...] = ("position", "orientation", "velocity")
    initial_theta: NDArray[np.floating] | None = None
    align_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate options are within valid ranges."""
        if self.max_iters <= 0:
            raise ValueError(f"max_iters must be positive: {self.max_iters}")
        if self.tol <= 0:
            raise ValueError(f"tol must be positive: {self.tol}")
        if self.regulariser < 0:
            raise ValueError(
                f"regulariser must be non-negative: {self.regulariser}"
            )
        if self.seed is not None and self.seed < 0:
            raise ValueError(f"seed must be non-negative: {self.seed}")
        valid_terms = {"position", "orientation", "velocity", "acceleration", "torque"}
        for term in self.cost_terms:
            if term not in valid_terms:
                raise ValueError(
                    f"Unknown cost term {term!r}. Valid: {sorted(valid_terms)}"
                )


# Type alias for target types
MultiSourceTarget = dict[str, Any]
ClubTarget = dict[str, Any]
ClubBallTarget = dict[str, Any]


@dataclass(frozen=True)
class FitResult:
    """Result from a motion matching fit.

    Attributes:
        theta: Fitted joint-angle trajectory (N, n_joints).
        target: The input target (so consumers can re-render).
        simulated_clubhead: Engine-rendered clubhead trace (N, 3).
        simulated_butt: Engine-rendered mid-hands trace (N, 3).
        cost_breakdown: Per-frame cost terms by name.
        metrics: Summary metrics.
        engine_name: Name of the engine that produced this result.
        engine_version: Version string of the engine.
        wall_time_s: Wall-clock time in seconds.
        n_iters: Number of optimization iterations.
        converged: Whether optimization converged.
    """

    theta: NDArray[np.floating]
    target: MultiSourceTarget | ClubTarget | ClubBallTarget
    simulated_clubhead: NDArray[np.floating]
    simulated_butt: NDArray[np.floating]
    cost_breakdown: dict[str, NDArray[np.floating]]
    metrics: FitMetrics
    engine_name: str
    engine_version: str
    wall_time_s: float
    n_iters: int
    converged: bool

    def __post_init__(self) -> None:
        """Validate result arrays and metrics."""
        if self.theta.ndim != 2:
            raise ValueError(f"theta must be 2D, got {self.theta.ndim}D")
        if self.simulated_clubhead.shape[1] != 3:
            raise ValueError(
                f"simulated_clubhead must have 3 columns, got {self.simulated_clubhead.shape[1]}"
            )
        if self.simulated_butt.shape[1] != 3:
            raise ValueError(
                f"simulated_butt must have 3 columns, got {self.simulated_butt.shape[1]}"
            )
        if not np.all(np.isfinite(self.theta)):
            raise ValueError("theta contains non-finite values")
        if not np.all(np.isfinite(self.simulated_clubhead)):
            raise ValueError("simulated_clubhead contains non-finite values")
        if not np.all(np.isfinite(self.simulated_butt)):
            raise ValueError("simulated_butt contains non-finite values")
        if self.wall_time_s < 0:
            raise ValueError(f"wall_time_s must be non-negative: {self.wall_time_s}")
        if self.n_iters < 0:
            raise ValueError(f"n_iters must be non-negative: {self.n_iters}")
        if not self.engine_name:
            raise ValueError("engine_name must be non-empty")