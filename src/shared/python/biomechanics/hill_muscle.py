"""Hill-type muscle model implementation.

This module implements a standard Hill-type muscle model commonly used in biomechanics
and robotics (e.g., OpenSim, MuJoCo).

Components:
1. Contractile Element (CE): Generates active force (f_l * f_v * a)
2. Parallel Elastic Element (PEE): Passive resistance to stretch
3. Series Elastic Element (SEE): Tendon elasticity

The total muscle-tendon force is:
F_mt = F_tendon = (F_CE + F_PEE) * cos(alpha)

Reference:
- Hill (1938), "The Heat of Shortening and the Dynamic Constants of Muscle"
- Zajac (1989), "Muscle and Tendon: Properties, Models, Scaling..."
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from src.shared.python.core.contracts import ensure, require
from src.shared.python.logging_pkg.logging_config import get_logger

logger = logging.getLogger(__name__)
logger = get_logger(__name__)


import upstream_muscle

@dataclass
class MuscleParameters:
    """Parameters defining a specific muscle."""

    F_max: float  # Maximum isometric force [N]
    l_opt: float  # Optimal fiber length [m]
    l_slack: float  # Tendon slack length [m]
    v_max: float = 10.0  # Max contraction velocity [l_opt/s] (default ~10)
    pennation_angle: float = 0.0  # Pennation angle at optimal length [rad]
    damping: float = 0.05  # Passive damping [N*s/m] (stabilization)

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.F_max <= 0:
            msg = "F_max must be positive"
            raise ValueError(msg)
        if self.l_opt <= 0:
            msg = "l_opt must be positive"
            raise ValueError(msg)
        if self.l_slack <= 0:
            msg = "l_slack must be positive"
            raise ValueError(msg)


@dataclass
class MuscleState:
    """Current state of the muscle."""

    activation: float = 0.0  # Current activation [0, 1]
    l_CE: float = 0.0  # Current fiber length [m]
    v_CE: float = 0.0  # Current fiber velocity [m/s]
    l_MT: float = 0.0  # Current muscle-tendon length [m]


class HillMuscleModel:
    """Standard Hill-type muscle model.

    Computes forces based on length, velocity, and activation.

    Force generation:
    F_CE = F_max * a * f_l(l_CE) * f_v(v_CE)
    F_PEE = F_max * f_p(l_CE)
    F_total = (F_CE + F_PEE) * cos(alpha)
    """

    #: Default width of the active force-length Gaussian curve.
    #: From Thelen (2003), J. Biomech. Eng., 125(1), pp. 70-77.
    DEFAULT_FORCE_LENGTH_WIDTH: float = 0.56

    def __init__(
        self,
        params: MuscleParameters,
        force_length_width: float | None = None,
    ) -> None:
        """Initialize muscle model.

        Args:
            params: MuscleParameters dataclass
            force_length_width: Width of the active force-length Gaussian
                curve (dimensionless). Default 0.56 from Thelen (2003).
        """
        self.params = params
        self._force_length_width = (
            force_length_width
            if force_length_width is not None
            else self.DEFAULT_FORCE_LENGTH_WIDTH
        )
        
        ru_params = upstream_muscle.MuscleParameters(
            f_max=params.F_max,
            l_opt=params.l_opt,
            l_slack=params.l_slack,
            v_max=params.v_max,
            pennation_angle=params.pennation_angle,
            damping=params.damping
        )
        self._rust_backend = upstream_muscle.HillMuscleModel(
            ru_params, 
            force_length_width=self._force_length_width
        )

    def force_length_active(self, l_norm: float) -> float:
        """Active force-length relationship (Gaussian-like curve).

        Args:
            l_norm: Normalized fiber length (l_CE / l_opt)

        Returns:
            Force multiplier [0, 1]
        """
        return self._rust_backend.force_length_active(l_norm)

    def force_length_passive(self, l_norm: float) -> float:
        """Passive force-length relationship (Exponential spring).

        Args:
            l_norm: Normalized fiber length (l_CE / l_opt)

        Returns:
            Force multiplier [0, inf)
        """
        return self._rust_backend.force_length_passive(l_norm)

    def force_velocity(self, v_norm: float) -> float:
        """Force-velocity relationship (Hill's Hyperbola).

        Args:
            v_norm: Normalized velocity (v_CE / v_max_m_s)
                   Positive = lengthening (eccentric)
                   Negative = shortening (concentric)

        Returns:
            Force multiplier [0, 1.8]
        """
        # Concentric (shortening)
        return self._rust_backend.force_velocity(v_norm)

    def tendon_force(self, l_tendon_norm: float) -> float:
        """Tendon force-length relationship (Non-linear spring).

        Args:
            l_tendon_norm: Normalized tendon length (l_tendon / l_slack)

        Returns:
            Force multiplier [0, inf)
        """
        return self._rust_backend.tendon_force(l_tendon_norm)

    def compute_force(self, state: MuscleState) -> float:
        """Compute total muscle force generated at the tendon.

        Design by Contract:
            Preconditions:
                - activation in [0, 1]
            Postconditions:
                - returned force >= 0

        Args:
            state: Current MuscleState

        Returns:
            Force at the tendon [N]
        """
        if not (state is not None):
            raise ValueError("state must be provided")
        if not (state is not None):
            raise ValueError("state must be provided")
        require(
            0.0 <= state.activation <= 1.0,
            "activation must be in [0, 1]",
            state.activation,
        )

        ru_state = upstream_muscle.MuscleState(
            activation=state.activation,
            l_ce=state.l_CE,
            v_ce=state.v_CE,
            l_mt=state.l_MT
        )
        return self._rust_backend.compute_force(ru_state)

    def compute_force_batch(
        self,
        activations: np.ndarray,
        l_ce: np.ndarray,
        v_ce: np.ndarray,
        l_mt: np.ndarray,
    ) -> np.ndarray:
        """Compute total muscle force for a batch of states.

        Args:
            activations: Array of activations [0, 1]
            l_ce: Array of fiber lengths [m]
            v_ce: Array of fiber velocities [m/s]
            l_mt: Array of muscle-tendon lengths [m]

        Returns:
            Array of forces at the tendon [N]
        """
        return self._rust_backend.compute_force_batch(
            activations, l_ce, v_ce, l_mt
        )


# Example usage
if __name__ == "__main__":
    # Define a generic muscle (e.g., Biceps)
    biceps_params = MuscleParameters(
        F_max=1000.0,
        l_opt=0.15,
        l_slack=0.20,
        v_max=10.0,
    )

    muscle = HillMuscleModel(biceps_params)

    # Test state
    state = MuscleState(
        activation=0.8,
        l_CE=0.15,
        v_CE=0.0,
        l_MT=0.35,  # At optimal length  # Isometric
    )

    force = muscle.compute_force(state)
    logger.info(f"Muscle force: {force:.1f} N")

    # Verify scaling
    F_muscle = muscle.compute_force(state)

    logger.info("Biceps muscle force test:")
    logger.info(f"  Activation: {state.activation * 100:.0f}%")
    logger.info(
        f"  Fiber length: {state.l_CE:.3f} m (opt: {biceps_params.l_opt:.3f} m)"
    )
    logger.info(f"  Fiber velocity: {state.v_CE:.3f} m/s")
    logger.info(f"  Force: {F_muscle:.1f} N (max: {biceps_params.F_max:.0f} N)")
    logger.info(f"  Force/F_max: {F_muscle / biceps_params.F_max * 100:.1f}%")
