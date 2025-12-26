
import sys
import os
import time
import numpy as np
from mujoco_humanoid_golf.rigid_body_dynamics.rnea import rnea
from mujoco_humanoid_golf.spatial_algebra.inertia import mci
from mujoco_humanoid_golf.spatial_algebra.transforms import xlt
from shared.python import constants

# Increase model size to exaggerate performance
NB = 50

def create_n_link_model(n):
    """Create a N-link planar robot for testing."""
    model = {
        "NB": n,
        "parent": np.arange(n) - 1,  # 0->-1, 1->0, 2->1 ...
        "jtype": ["Rz"] * n,
        "gravity": np.array([0, 0, 0, 0, -constants.GRAVITY_M_S2, 0]),
    }

    # Link parameters
    L = 1.0
    m = 1.0
    I = (1 / 12) * m * L**2

    # Joint transforms
    model["Xtree"] = [np.eye(6)] + [xlt(np.array([L, 0, 0]))] * (n - 1)

    # Spatial inertias
    com = np.array([L / 2, 0, 0])
    I_rot = np.diag([0, 0, I])
    I_spatial = mci(m, com, I_rot)

    model["I"] = [I_spatial] * n

    return model

def benchmark():
    model = create_n_link_model(NB)
    q = np.random.rand(NB)
    qd = np.random.rand(NB)
    qdd = np.random.rand(NB)

    # Warmup
    for _ in range(100):
        rnea(model, q, qd, qdd)

    iterations = 2000
    start_time = time.time()
    for _ in range(iterations):
        rnea(model, q, qd, qdd)
    end_time = time.time()

    avg_time = (end_time - start_time) / iterations * 1000
    print(f"Average time per RNEA call ({NB} links): {avg_time:.4f} ms")

if __name__ == "__main__":
    benchmark()
