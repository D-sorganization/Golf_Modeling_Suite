import numpy as np
import pytest

from src.shared.python.biomechanics.activation_dynamics import ActivationDynamics as PyActivationDynamics
from src.shared.python.biomechanics.hill_muscle import HillMuscleModel as PyHillMuscleModel
from src.shared.python.biomechanics.hill_muscle import MuscleParameters as PyMuscleParameters
from src.shared.python.biomechanics.hill_muscle import MuscleState as PyMuscleState

import upstream_muscle

def test_activation_dynamics_parity():
    py_ad = PyActivationDynamics(tau_act=0.010, tau_deact=0.040, min_activation=0.001)
    ru_ad = upstream_muscle.ActivationDynamics(tau_act=0.010, tau_deact=0.040, min_activation=0.001)
    
    np.random.seed(42)
    u_vals = np.random.uniform(0, 1, 100)
    a_vals = np.random.uniform(0, 1, 100)
    
    dt = 0.001
    ru_a_nexts = ru_ad.update_batch(u_vals.tolist(), a_vals.tolist(), dt)
    
    for i in range(100):
        py_a_next = py_ad.update(float(u_vals[i]), float(a_vals[i]), dt)
        np.testing.assert_allclose(py_a_next, ru_a_nexts[i], rtol=1e-5, atol=1e-8)

def test_hill_muscle_parity():
    # Params
    f_max = 1000.0
    l_opt = 0.15
    l_slack = 0.20
    v_max = 10.0
    pennation_angle = 0.1
    damping = 0.05
    
    py_params = PyMuscleParameters(F_max=f_max, l_opt=l_opt, l_slack=l_slack, v_max=v_max, pennation_angle=pennation_angle, damping=damping)
    ru_params = upstream_muscle.MuscleParameters(f_max, l_opt, l_slack, v_max, pennation_angle, damping)
    
    py_model = PyHillMuscleModel(py_params)
    ru_model = upstream_muscle.HillMuscleModel(ru_params)
    
    np.random.seed(42)
    activations = np.random.uniform(0, 1, 100)
    l_ces = np.random.uniform(0.05, 0.3, 100)
    v_ces = np.random.uniform(-5.0, 5.0, 100)
    
    ru_states = []
    for i in range(100):
        ru_states.append(upstream_muscle.MuscleState(
            activation=float(activations[i]),
            l_ce=float(l_ces[i]),
            v_ce=float(v_ces[i]),
            l_mt=0.35
        ))
        
    ru_forces = ru_model.compute_force_batch(ru_states)
    
    for i in range(100):
        py_state = PyMuscleState(
            activation=float(activations[i]),
            l_CE=float(l_ces[i]),
            v_CE=float(v_ces[i]),
            l_MT=0.35
        )
        py_f = py_model.compute_force(py_state)
        np.testing.assert_allclose(py_f, ru_forces[i], rtol=1e-5, atol=1e-8)
