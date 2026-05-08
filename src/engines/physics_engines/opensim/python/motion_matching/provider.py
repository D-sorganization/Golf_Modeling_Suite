"""OpenSim ``FitSwingProvider`` adapter (issue #4518).

Wraps the existing prescribed-controller / SLSQP fit pipeline
(:func:`fit_swing_opensim`) in the canonical engine-agnostic
:class:`FitSwingProvider` contract introduced by issue #4514.

The recent prescribed-controller fixes pinned by issues #4322, #4326, and
#4327 live entirely inside :mod:`prescribed_controller` and
:mod:`simulate`; this adapter only adapts I/O, never reaches into the
controller plumbing.

Public API:
    OpenSimFitSwingProvider -- adapter satisfying :class:`FitSwingProvider`.
"""

from __future__ import annotations

import time as _time
from collections.abc import Callable
import numpy as np
from numpy.typing import NDArray

from src.shared.python.motion_matching.club_target import ClubTarget
from src.shared.python.motion_matching.cost import SimOutput
from src.shared.python.motion_matching.fit_swing import (
    FitMetrics,
    FitOptions,
    FitTarget,
)
from src.shared.python.motion_matching.fit_swing import FitResult as FitSwingResult

__all__ = ["OpenSimFitSwingProvider"]


def _opensim_version() -> str:
    """Return the installed OpenSim version, or ``"unknown"`` if unavailable."""
    try:  # pragma: no cover - branch depends on env
        import opensim  # type: ignore[import-not-found]

        v = getattr(opensim, "__version__", None)
        if isinstance(v, str) and v:
            return v
    except ImportError:
        pass
    return "unknown"


class OpenSimFitSwingProvider:
    """Engine adapter exposing OpenSim's fit pipeline on the canonical API.

    The adapter delegates to :func:`fit_swing_opensim`, then converts its
    polynomial-coefficient :class:`CanonicalFitResult` plus a forward roll-out
    of the recovered controller into the engine-agnostic
    :class:`FitSwingResult` schema.

    Attributes:
        engine_name: Always ``"opensim"``.
        engine_version: Populated from ``opensim.__version__`` at construction
            time, or ``"unknown"`` if the wheel is not importable.
    """

    engine_name: str = "opensim"

    def __init__(
        self,
        simulate_fn: Callable[[NDArray[np.float64]], SimOutput] | None = None,
    ) -> None:
        """Construct the provider.

        Args:
            simulate_fn: Optional forward simulator override. When ``None``,
                the OpenSim ``simulate_with_coefficients`` wrapper is used at
                fit time (which itself requires the ``opensim`` wheel).
                Tests inject a deterministic kinematic mock here.
        """
        self.engine_version = _opensim_version()
        self._simulate_fn = simulate_fn

    # ------------------------------------------------------------------ #
    # FitSwingProvider protocol
    # ------------------------------------------------------------------ #

    def supports_body_target(self) -> bool:
        """OpenSim fit pipeline currently only supports :class:`ClubTarget`."""
        return False

    def supports_ball_target(self) -> bool:
        """OpenSim fit pipeline currently does not target ball trajectories."""
        return False

    def fit_swing(
        self,
        target: FitTarget,
        opts: FitOptions,
    ) -> FitSwingResult:
        """Fit polynomial torque coefficients to ``target``.

        Args:
            target: Canonical :class:`ClubTarget`. :class:`BodyTarget` is not
                yet supported (see :meth:`supports_body_target`).
            opts: :class:`FitOptions`. ``max_iters``, ``tol``, ``seed``, and
                ``initial_theta`` are forwarded to the SLSQP driver.

        Returns:
            :class:`FitSwingResult` with theta in ``(N, n_joints)`` shape,
            simulated clubhead / butt traces, per-frame cost breakdown,
            summary metrics, and engine metadata.

        Raises:
            TypeError:  If ``target`` is not a :class:`ClubTarget`.
            ValueError: On invalid options (bubbled from the SLSQP driver).
        """
        if not isinstance(target, ClubTarget):
            raise TypeError(
                "OpenSimFitSwingProvider.fit_swing currently requires a "
                f"ClubTarget; got {type(target).__name__}"
            )
        if not isinstance(opts, FitOptions):
            raise TypeError(f"opts must be FitOptions; got {type(opts).__name__}")

        # Lazy import: keeps the package importable without scipy etc. at
        # registration time and avoids a hard dependency from this file.
        from src.engines.physics_engines.opensim.python.motion_matching.fit_swing import (
            FitOptions as OpenSimFitOptions,
        )
        from src.engines.physics_engines.opensim.python.motion_matching.fit_swing import (
            fit_swing_opensim,
        )

        n_joints, theta0 = self._resolve_n_joints_and_theta0(opts)
        os_opts = OpenSimFitOptions(
            max_iter=int(opts.max_iters),
            ftol=float(opts.tol),
            n_joints=n_joints,
            theta0=theta0,
            rng_seed=int(opts.seed) if opts.seed is not None else 42,
            simulate_fn=self._simulate_fn,
        )

        t0 = _time.perf_counter()
        os_result = fit_swing_opensim(target, os_opts)
        wall_time_s = _time.perf_counter() - t0

        # Forward roll-out of the recovered theta so we can populate the
        # canonical (N, n_joints) trajectory and (N, 3) clubhead/butt traces.
        sim_fn = self._simulate_fn or _default_simulate_fn()
        sim_out = sim_fn(np.asarray(os_result.theta_optimal, dtype=np.float64))
        n_frames = int(sim_out.clubhead.shape[0])

        # Theta in (N, n_joints) form: tile the polynomial coefficients across
        # frames so callers can re-render via the cross-engine surrogate. The
        # canonical schema asks for joint angles per frame; for an engine that
        # parameterises by polynomial torque coefficients, the per-frame
        # broadcast preserves shape contract while remaining recoverable.
        theta_flat = np.asarray(os_result.theta_optimal, dtype=np.float64)
        # The driver may infer ``n_joints`` from the simulator hint when the
        # caller leaves it ``None``; recover the actual count from the flat
        # vector length so the canonical (N, n_joints*7) shape is honest.
        d = theta_flat.size
        theta_2d = np.tile(theta_flat[:d], (n_frames, 1)).astype(np.float64)

        clubhead = np.ascontiguousarray(sim_out.clubhead, dtype=np.float64)
        butt = np.ascontiguousarray(sim_out.butt, dtype=np.float64)

        per_frame_err = np.linalg.norm(clubhead - target.clubhead, axis=1)
        rmse = float(np.sqrt(np.mean(per_frame_err**2)))
        max_err = float(np.max(per_frame_err))

        toi_err_s = self._time_of_impact_error(sim_out, target)

        metrics = FitMetrics(
            rmse_clubhead=rmse,
            max_clubhead_error_m=max_err,
            time_of_impact_error_s=toi_err_s,
            convergence_norm=float(os_result.final_cost),
        )

        cost_breakdown: dict[str, NDArray[np.float64]] = {
            "clubhead_position": per_frame_err.astype(np.float64),
        }

        return FitSwingResult(
            theta=theta_2d,
            target=target,
            simulated_clubhead=clubhead,
            simulated_butt=butt,
            cost_breakdown=cost_breakdown,
            metrics=metrics,
            engine_name=self.engine_name,
            engine_version=self.engine_version,
            wall_time_s=float(wall_time_s),
            n_iters=int(os_result.iterations),
            converged=bool(os_result.solver_status == "success"),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _resolve_n_joints_and_theta0(
        opts: FitOptions,
    ) -> tuple[int | None, NDArray[np.float64] | None]:
        """Translate canonical ``initial_theta`` into the OpenSim driver shape.

        The OpenSim driver expects a flat ``(n_joints * 7,)`` polynomial
        coefficient vector. The canonical ``FitOptions.initial_theta`` is
        either flat or 2-D ``(N, n_joints)``; we forward only the flat form
        (a 2-D array is interpreted as ``n_joints`` columns and 7 polynomial
        rows are not implied, so we leave warm-start to the driver default).
        """
        if opts.initial_theta is None:
            return None, None
        arr = np.asarray(opts.initial_theta, dtype=np.float64)
        if arr.ndim == 1:
            d = arr.size
            if d % 7 != 0:
                # Not a polynomial-coefficient vector; let the driver default
                # warm-start fire.
                return None, None
            return d // 7, arr.reshape(-1).copy()
        # 2-D: treat first row as the warm-start polynomial coefficients.
        flat = arr[0].astype(np.float64, copy=True)
        d = flat.size
        if d % 7 != 0:
            return None, None
        return d // 7, flat

    @staticmethod
    def _time_of_impact_error(sim_out: SimOutput, target: ClubTarget) -> float:
        """Signed seconds between simulated and target clubhead-speed peak."""
        if sim_out.time is None:
            return 0.0
        time = np.asarray(sim_out.time, dtype=np.float64).reshape(-1)
        n = min(time.size, sim_out.clubhead.shape[0])
        if n < 2:
            return 0.0
        ch = sim_out.clubhead[:n]
        speed = np.linalg.norm(np.diff(ch, axis=0), axis=1) / np.maximum(
            np.diff(time[:n]), 1e-9
        )
        sim_impact_idx = int(np.argmax(speed))
        target_impact_idx = int(target.impact_idx)
        sim_impact_idx = min(sim_impact_idx, time.size - 1)
        target_impact_idx = min(target_impact_idx, target.time.size - 1)
        return float(time[sim_impact_idx] - target.time[target_impact_idx])


def _default_simulate_fn() -> Callable[[NDArray[np.float64]], SimOutput]:
    """Return the OpenSim default forward simulator (``simulate_with_coefficients``)."""
    from src.engines.physics_engines.opensim.python.motion_matching.simulate import (
        simulate_with_coefficients,
    )

    return simulate_with_coefficients  # type: ignore[return-value]
