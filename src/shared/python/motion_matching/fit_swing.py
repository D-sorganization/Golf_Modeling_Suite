"""Canonical engine-side ``fit_swing`` API (issue #4514).

This module defines the contract every physics engine must implement so the
cross-engine matcher / leaderboard / diagnostics can talk to Drake, MuJoCo,
Pinocchio, OpenSim, MyoSim, and Simscape with one set of types.

Public API:
    FitSwingProvider   -- runtime-checkable ``Protocol`` for engine adapters.
    FitOptions         -- dataclass extending :class:`AlignOptions` with
                          optimisation knobs.
    FitMetrics         -- frozen dataclass of summary RMSE / max-error / TOI.
    FitResult          -- frozen dataclass returned by ``fit_swing``.
    CostTerm           -- enum of supported cost-function terms.
    FitTarget          -- :class:`Union` accepted by ``fit_swing``.

See the companion :mod:`provider_registry` module for runtime discovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from .body_target import BodyTarget
from .target import AlignOptions, ClubTarget

if TYPE_CHECKING:
    pass

__all__ = [
    "CostTerm",
    "FitMetrics",
    "FitOptions",
    "FitResult",
    "FitSwingProvider",
    "FitTarget",
]


# ---------------------------------------------------------------------------
# Target union
# ---------------------------------------------------------------------------

# ``MultiSourceTarget`` and ``ClubBallTarget`` are forthcoming sibling targets
# (tracked separately). Until they land, ``FitTarget`` is the union of the
# canonical targets that already exist in the package. Engines that only
# support a subset advertise via ``supports_body_target`` /
# ``supports_ball_target``.
FitTarget = ClubTarget | BodyTarget


# ---------------------------------------------------------------------------
# Cost terms
# ---------------------------------------------------------------------------


class CostTerm(str, Enum):
    """Supported cost-function terms.

    Engines may accept a subset; unknown terms must raise ``ValueError``.
    """

    CLUBHEAD_POSITION = "clubhead_position"
    BUTT_POSITION = "butt_position"
    CLUB_ORIENTATION = "club_orientation"
    BODY_POSITION = "body_position"
    BALL_POSITION = "ball_position"
    EFFORT = "effort"
    SMOOTHNESS = "smoothness"
    REGULARISER = "regulariser"


# ---------------------------------------------------------------------------
# FitOptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FitOptions:
    """Optimisation knobs for a single ``fit_swing`` call.

    Composes :class:`AlignOptions` (resampling / impact alignment) rather than
    inheriting from it -- frozen dataclasses cannot extend each other safely.

    Attributes:
        align: Time-alignment / resampling options applied to the target.
        max_iters: Hard upper bound on optimiser iterations. Must be > 0.
        tol: Convergence tolerance on the cost gradient or step norm.
            Must be finite and >= 0.
        seed: RNG seed for any stochastic step (e.g. multi-start). ``None``
            means engine-chosen.
        regulariser: Free-form regulariser identifier
            (e.g. ``"l2"``, ``"sobolev"``, ``"none"``). Must be a non-empty
            string.
        cost_terms: ``frozenset`` of :class:`CostTerm` to include. Must be
            non-empty.
        initial_theta: Optional warm-start ``(n_joints,)`` or
            ``(N, n_joints)`` array. ``None`` means engine default.
    """

    align: AlignOptions = field(default_factory=AlignOptions)
    max_iters: int = 100
    tol: float = 1e-6
    seed: int | None = None
    regulariser: str = "l2"
    cost_terms: frozenset[CostTerm] = field(
        default_factory=lambda: frozenset({CostTerm.CLUBHEAD_POSITION})
    )
    initial_theta: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Validate every field at construction (DbC)."""
        if not isinstance(self.align, AlignOptions):
            raise TypeError(
                f"FitOptions.align must be AlignOptions, got {type(self.align)!r}"
            )
        if not isinstance(self.max_iters, int) or self.max_iters <= 0:
            raise ValueError(
                f"FitOptions.max_iters must be a positive int; got {self.max_iters!r}"
            )
        if not np.isfinite(self.tol) or self.tol < 0.0:
            raise ValueError(
                f"FitOptions.tol must be finite and >= 0; got {self.tol!r}"
            )
        if self.seed is not None and (not isinstance(self.seed, int) or self.seed < 0):
            raise ValueError(
                f"FitOptions.seed must be None or a non-negative int; got {self.seed!r}"
            )
        if not isinstance(self.regulariser, str) or not self.regulariser:
            raise ValueError(
                "FitOptions.regulariser must be a non-empty string; "
                f"got {self.regulariser!r}"
            )
        if not isinstance(self.cost_terms, frozenset):
            raise TypeError(
                "FitOptions.cost_terms must be a frozenset of CostTerm; "
                f"got {type(self.cost_terms)!r}"
            )
        if not self.cost_terms:
            raise ValueError("FitOptions.cost_terms must be non-empty")
        for term in self.cost_terms:
            if not isinstance(term, CostTerm):
                raise TypeError(
                    f"FitOptions.cost_terms entries must be CostTerm; got {term!r}"
                )
        if self.initial_theta is not None:
            if not isinstance(self.initial_theta, np.ndarray):
                raise TypeError(
                    "FitOptions.initial_theta must be np.ndarray or None; "
                    f"got {type(self.initial_theta)!r}"
                )
            if self.initial_theta.ndim not in (1, 2):
                raise ValueError(
                    "FitOptions.initial_theta must be 1-D or 2-D; "
                    f"got shape {self.initial_theta.shape}"
                )
            if not np.all(np.isfinite(self.initial_theta)):
                raise ValueError("FitOptions.initial_theta contains NaN or Inf")


# ---------------------------------------------------------------------------
# FitMetrics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FitMetrics:
    """Summary metrics for a single fit run.

    All scalars must be finite and non-negative.

    Attributes:
        rmse_clubhead: Root-mean-square clubhead position error (metres).
        max_clubhead_error_m: Peak clubhead position error (metres).
        time_of_impact_error_s: Signed seconds between simulated and target
            impact event. May be negative; absolute value must be finite.
        convergence_norm: Final gradient / step norm reported by the
            optimiser. Non-negative.
    """

    rmse_clubhead: float
    max_clubhead_error_m: float
    time_of_impact_error_s: float
    convergence_norm: float

    def __post_init__(self) -> None:
        """Validate every metric is finite (DbC)."""
        for name, value in (
            ("rmse_clubhead", self.rmse_clubhead),
            ("max_clubhead_error_m", self.max_clubhead_error_m),
            ("time_of_impact_error_s", self.time_of_impact_error_s),
            ("convergence_norm", self.convergence_norm),
        ):
            if not np.isfinite(value):
                raise ValueError(f"FitMetrics.{name} must be finite; got {value!r}")
        for name, value in (
            ("rmse_clubhead", self.rmse_clubhead),
            ("max_clubhead_error_m", self.max_clubhead_error_m),
            ("convergence_norm", self.convergence_norm),
        ):
            if value < 0.0:
                raise ValueError(f"FitMetrics.{name} must be >= 0; got {value!r}")


# ---------------------------------------------------------------------------
# FitResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FitResult:
    """Engine-agnostic result of a ``fit_swing`` call.

    Attributes:
        theta: Fitted joint-angle trajectory ``(N, n_joints)``, float64.
        target: The :class:`FitTarget` that was fit to (for re-rendering).
        simulated_clubhead: Engine-rendered clubhead trace ``(N, 3)``.
        simulated_butt: Engine-rendered mid-hands trace ``(N, 3)``.
        cost_breakdown: Per-frame cost terms keyed by name. Every value is a
            1-D float array of length ``N``.
        metrics: Summary :class:`FitMetrics`.
        engine_name: Engine identifier (e.g. ``"drake"``).
        engine_version: Free-form engine version string. Non-empty.
        wall_time_s: Wallclock seconds. Finite, >= 0.
        n_iters: Optimiser iterations consumed. Int, >= 0.
        converged: Whether the optimiser hit its tolerance.
    """

    theta: NDArray[np.float64]
    target: FitTarget
    simulated_clubhead: NDArray[np.float64]
    simulated_butt: NDArray[np.float64]
    cost_breakdown: dict[str, NDArray[np.float64]]
    metrics: FitMetrics
    engine_name: str
    engine_version: str
    wall_time_s: float
    n_iters: int
    converged: bool

    def __post_init__(self) -> None:
        """Validate shapes, finiteness, and metadata (DbC)."""
        if not isinstance(self.theta, np.ndarray):
            raise TypeError(
                f"FitResult.theta must be np.ndarray; got {type(self.theta)!r}"
            )
        if self.theta.ndim != 2:
            raise ValueError(
                f"FitResult.theta must be 2-D (N, n_joints); "
                f"got shape {self.theta.shape}"
            )
        n_frames = self.theta.shape[0]
        if n_frames < 1:
            raise ValueError("FitResult.theta must have at least one frame")
        if not np.all(np.isfinite(self.theta)):
            raise ValueError("FitResult.theta contains NaN or Inf")

        for name, arr in (
            ("simulated_clubhead", self.simulated_clubhead),
            ("simulated_butt", self.simulated_butt),
        ):
            if not isinstance(arr, np.ndarray):
                raise TypeError(
                    f"FitResult.{name} must be np.ndarray; got {type(arr)!r}"
                )
            if arr.shape != (n_frames, 3):
                raise ValueError(
                    f"FitResult.{name} must have shape ({n_frames}, 3); got {arr.shape}"
                )
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"FitResult.{name} contains NaN or Inf")

        if not isinstance(self.cost_breakdown, dict):
            raise TypeError(
                "FitResult.cost_breakdown must be a dict[str, np.ndarray]; "
                f"got {type(self.cost_breakdown)!r}"
            )
        for key, value in self.cost_breakdown.items():
            if not isinstance(key, str) or not key:
                raise ValueError(
                    "FitResult.cost_breakdown keys must be non-empty strings; "
                    f"got {key!r}"
                )
            if not isinstance(value, np.ndarray):
                raise TypeError(
                    f"FitResult.cost_breakdown[{key!r}] must be np.ndarray; "
                    f"got {type(value)!r}"
                )
            if value.shape != (n_frames,):
                raise ValueError(
                    f"FitResult.cost_breakdown[{key!r}] must have shape "
                    f"({n_frames},); got {value.shape}"
                )
            if not np.all(np.isfinite(value)):
                raise ValueError(
                    f"FitResult.cost_breakdown[{key!r}] contains NaN or Inf"
                )

        if not isinstance(self.metrics, FitMetrics):
            raise TypeError(
                f"FitResult.metrics must be FitMetrics; got {type(self.metrics)!r}"
            )

        if not isinstance(self.engine_name, str) or not self.engine_name:
            raise ValueError("FitResult.engine_name must be a non-empty string")
        if not isinstance(self.engine_version, str) or not self.engine_version:
            raise ValueError("FitResult.engine_version must be a non-empty string")

        if not np.isfinite(self.wall_time_s) or self.wall_time_s < 0.0:
            raise ValueError(
                f"FitResult.wall_time_s must be finite and >= 0; "
                f"got {self.wall_time_s!r}"
            )
        if not isinstance(self.n_iters, int) or self.n_iters < 0:
            raise ValueError(
                f"FitResult.n_iters must be a non-negative int; got {self.n_iters!r}"
            )
        if not isinstance(self.converged, bool):
            raise TypeError(
                f"FitResult.converged must be bool; got {type(self.converged)!r}"
            )


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class FitSwingProvider(Protocol):
    """Engine-side motion-matching entry point.

    Every physics engine ships an adapter object satisfying this protocol and
    registers it with :mod:`provider_registry`. The matcher discovers
    available engines via :func:`available_engines` and dispatches by
    ``engine_name``.

    Attributes:
        engine_name: Lowercase identifier
            (``"drake"`` | ``"mujoco"`` | ``"pinocchio"`` | ``"opensim"`` |
            ``"myosim"`` | ``"simscape"`` | ...).
    """

    engine_name: str

    def fit_swing(
        self,
        target: FitTarget,
        opts: FitOptions,
    ) -> FitResult:
        """Fit ``theta`` such that the engine reproduces ``target``."""
        ...

    def supports_body_target(self) -> bool:
        """Whether this engine can fit a :class:`BodyTarget`."""
        ...

    def supports_ball_target(self) -> bool:
        """Whether this engine can fit a ball-trajectory target."""
        ...
