"""Numerical helpers for kinematic force analysis."""

from __future__ import annotations

import warnings

import numpy as np

from src.shared.python.core.numerical_constants import EPSILON_SINGULARITY_DETECTION


def normalize_effective_mass_direction(direction: np.ndarray) -> np.ndarray:
    """Normalize an effective-mass direction or raise on singular input."""
    direction_norm = np.linalg.norm(direction)
    if direction_norm < EPSILON_SINGULARITY_DETECTION:
        raise ValueError(
            f"Direction vector has near-zero magnitude: {direction_norm:.2e}. "
            "Cannot compute effective mass for zero-length direction."
        )
    return direction / direction_norm


def check_mass_matrix_conditioning(M: np.ndarray) -> None:
    """Warn or raise when the mass matrix is numerically unsafe."""
    M_cond = np.linalg.cond(M)
    if M_cond > 1e6:
        warnings.warn(
            f"Mass matrix is ill-conditioned: k(M) = {M_cond:.2e} > 1e6. "
            "Effective mass computation may be numerically unstable. "
            "This often indicates the robot is near a kinematic singularity.",
            category=UserWarning,
            stacklevel=2,
        )

    eigenvalues = np.linalg.eigvalsh(M)
    if np.any(eigenvalues <= 0):
        raise ValueError(
            "Mass matrix is not positive definite. "
            f"Minimum eigenvalue: {eigenvalues.min():.2e}. "
            "This indicates a modeling error or numerical instability."
        )


def check_jacobian_rank(jacp: np.ndarray) -> None:
    """Warn when the translational Jacobian loses rank."""
    J_rank = np.linalg.matrix_rank(jacp)
    if J_rank < 3:
        warnings.warn(
            f"Jacobian is rank deficient: rank={J_rank} < 3. "
            "Robot has lost mobility in some directions. "
            "Effective mass may not be well-defined.",
            category=RuntimeWarning,
            stacklevel=2,
        )


def compute_effective_mass_value(
    direction: np.ndarray,
    jacp: np.ndarray,
    M: np.ndarray,
) -> float:
    """Compute a scalar effective mass with singularity guards."""
    J_dir = direction @ jacp
    M_inv = np.linalg.inv(M)
    denominator = J_dir @ M_inv @ J_dir.T + EPSILON_SINGULARITY_DETECTION

    if abs(denominator) < 1e-8:
        warnings.warn(
            f"Effective mass denominator near zero: {denominator:.2e}. "
            "Robot is at or very close to a kinematic singularity in the "
            f"specified direction {direction}. Effective mass is extremely large.",
            category=UserWarning,
            stacklevel=2,
        )

    m_eff = 1.0 / denominator

    if m_eff < 0:
        raise ValueError(
            f"Computed negative effective mass: {m_eff:.2e} kg. "
            "This indicates a numerical error or modeling issue."
        )

    if not np.isfinite(m_eff):
        warnings.warn(
            f"Effective mass is non-finite: {m_eff}. "
            "Robot is at a kinematic singularity. "
            "Returning large finite value instead.",
            category=UserWarning,
            stacklevel=2,
        )
        m_eff = 1e10

    return float(m_eff)


def decompose_apparent_force(
    apparent_force: np.ndarray,
    body_position: np.ndarray,
) -> np.ndarray:
    """Project an apparent force onto the body's radial direction."""
    centrifugal_direction = body_position / (
        np.linalg.norm(body_position) + EPSILON_SINGULARITY_DETECTION
    )
    centrifugal_magnitude = np.dot(apparent_force, centrifugal_direction)
    return centrifugal_magnitude * centrifugal_direction
