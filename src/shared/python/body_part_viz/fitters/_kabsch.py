"""Kabsch / Procrustes helpers for cluster fitters.

Pure-NumPy implementation of the Kabsch algorithm with a reflection
guard. Lives in its own module so multiple fitters can reuse it without
importing from each other.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

__all__ = ["kabsch_rotation", "anisotropic_scale"]


def kabsch_rotation(
    p: NDArray[np.floating],
    q: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Return the proper rotation ``R`` mapping centred ``p`` onto ``q``.

    Solves ``min_R || R @ p.T - q.T ||_F`` subject to ``R^T R = I`` and
    ``det(R) = +1``. Inputs must already be centred (zero mean).

    Args:
        p: ``(N, 3)`` source points (centred).
        q: ``(N, 3)`` target points (centred).

    Returns:
        ``(3, 3)`` rotation matrix with ``det(R) == +1``.

    Raises:
        ValueError: If ``p`` and ``q`` do not have matching ``(N, 3)`` shape
            or ``N < 1``.
    """
    if p.shape != q.shape:
        raise ValueError(
            f"p and q must have the same shape, got {p.shape} vs {q.shape}"
        )
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError(f"p and q must have shape (N, 3), got {p.shape}")
    if p.shape[0] < 1:
        raise ValueError("Kabsch requires at least one point")

    h = p.T @ q
    u, _s, vt = np.linalg.svd(h)

    d = np.sign(np.linalg.det(vt.T @ u.T))
    if d == 0.0:
        d = 1.0
    diag = np.array([1.0, 1.0, d], dtype=float)
    rotation = vt.T @ np.diag(diag) @ u.T
    return rotation


def anisotropic_scale(
    p_rot: NDArray[np.floating],
    q: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Return ``(sx, sy, sz)`` minimising ``|| diag(s) p_rot.T - q.T ||_F``.

    Args:
        p_rot: ``(N, 3)`` rotated source (centred).
        q: ``(N, 3)`` target (centred).

    Returns:
        ``(3,)`` strictly positive scale vector. Each component falls back
        to ``1.0`` if the corresponding axis has near-zero variance in the
        source (degenerate case).
    """
    s = np.ones(3, dtype=float)
    for axis in range(3):
        denom = float(np.sum(p_rot[:, axis] * p_rot[:, axis]))
        numer = float(np.sum(p_rot[:, axis] * q[:, axis]))
        if denom > 1e-12:
            value = numer / denom
            if not np.isfinite(value) or value <= 0.0:
                s[axis] = 1.0
            else:
                s[axis] = value
        else:
            s[axis] = 1.0
    return s
