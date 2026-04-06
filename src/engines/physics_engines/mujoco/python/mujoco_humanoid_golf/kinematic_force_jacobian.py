"""Jacobian helpers for kinematic force analysis."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np


@dataclass(slots=True)
class JacobianBuffers:
    """Pre-allocated Jacobian buffers plus API-shape metadata."""

    use_reshaped_arrays: bool
    jacp: np.ndarray
    jacr: np.ndarray
    nv: int


def initialize_jacobian_buffers(
    model: mujoco.MjModel,
    data: mujoco.MjData,
) -> JacobianBuffers:
    """Allocate Jacobian buffers that match the active MuJoCo API."""
    nv = model.nv
    try:
        jacp = np.zeros((3, nv))
        jacr = np.zeros((3, nv))
        mujoco.mj_jacBody(model, data, jacp, jacr, 0)
        return JacobianBuffers(
            use_reshaped_arrays=True,
            jacp=jacp,
            jacr=jacr,
            nv=nv,
        )
    except TypeError:
        return JacobianBuffers(
            use_reshaped_arrays=False,
            jacp=np.zeros(3 * nv),
            jacr=np.zeros(3 * nv),
            nv=nv,
        )


def compute_body_jacobian(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_id: int,
    buffers: JacobianBuffers,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute a body Jacobian using reusable buffers."""
    mujoco.mj_jacBody(model, data, buffers.jacp, buffers.jacr, body_id)
    if buffers.use_reshaped_arrays:
        return buffers.jacp, buffers.jacr

    return buffers.jacp.reshape(3, buffers.nv), buffers.jacr.reshape(3, buffers.nv)


def compute_jacobian_central_difference(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_id: int,
    qpos: np.ndarray,
    qvel: np.ndarray,
    epsilon: float,
    buffers: JacobianBuffers,
) -> tuple[np.ndarray, np.ndarray]:
    """Approximate J and Jdot for a body via central difference in qpos."""
    data.qpos[:] = qpos
    data.qvel[:] = qvel
    mujoco.mj_forward(model, data)
    jacp_curr, _ = compute_body_jacobian(model, data, body_id, buffers)
    jacp_curr = jacp_curr.copy()
    body_position = data.xpos[body_id].copy()

    data.qpos[:] = qpos + epsilon * qvel
    data.qvel[:] = qvel
    mujoco.mj_forward(model, data)
    jacp_forward, _ = compute_body_jacobian(model, data, body_id, buffers)
    jacp_forward = jacp_forward.copy()

    data.qpos[:] = qpos - epsilon * qvel
    data.qvel[:] = qvel
    mujoco.mj_forward(model, data)
    jacp_backward, _ = compute_body_jacobian(model, data, body_id, buffers)

    jacp_dot = (jacp_forward - jacp_backward) / (2.0 * epsilon)
    return jacp_curr, jacp_dot, body_position
