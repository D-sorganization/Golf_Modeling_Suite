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
    l_mts = np.full(100, 0.35)
    
    ru_forces = ru_model.compute_force_batch(activations, l_ces, v_ces, l_mts)
    
    for i in range(100):
        py_state = PyMuscleState(
            activation=float(activations[i]),
            l_CE=float(l_ces[i]),
            v_CE=float(v_ces[i]),
            l_MT=0.35
        )
        py_f = py_model.compute_force(py_state)
        np.testing.assert_allclose(py_f, ru_forces[i], rtol=1e-5, atol=1e-8)

def test_equilibrium_parity():
    from src.shared.python.biomechanics.muscle_equilibrium import EquilibriumSolver as PyEquilibriumSolver
    
    f_max = 1000.0
    l_opt = 0.12
    l_slack = 0.25
    v_max = 1.2
    
    py_params = PyMuscleParameters(F_max=f_max, l_opt=l_opt, l_slack=l_slack, v_max=v_max)
    ru_params = upstream_muscle.MuscleParameters(f_max, l_opt, l_slack, v_max, 0.0, 0.05)
    
    py_model = PyHillMuscleModel(py_params)
    ru_model = upstream_muscle.HillMuscleModel(ru_params)
    
    py_solver = PyEquilibriumSolver(py_model)
    ru_solver = upstream_muscle.EquilibriumSolver(ru_model)
    
    np.random.seed(42)
    l_mts = np.random.uniform(l_opt + l_slack - 0.05, l_opt + l_slack + 0.05, 10)
    activations = np.random.uniform(0.1, 1.0, 10)
    
    for i in range(10):
        py_l_ce = py_solver.solve_fiber_length(float(l_mts[i]), float(activations[i]))
        ru_l_ce = ru_solver.solve_fiber_length(float(l_mts[i]), float(activations[i]))
        np.testing.assert_allclose(py_l_ce, ru_l_ce, rtol=1e-5, atol=1e-6)
        
        py_v_ce = py_solver.solve_fiber_velocity(float(l_mts[i]), 0.1, float(activations[i]), py_l_ce)
        ru_v_ce = ru_solver.solve_fiber_velocity(float(l_mts[i]), 0.1, float(activations[i]), ru_l_ce)
        np.testing.assert_allclose(py_v_ce, ru_v_ce, rtol=1e-5, atol=1e-6)

def test_multi_muscle_parity():
    from src.shared.python.biomechanics.multi_muscle import MuscleGroup as PyMuscleGroup
    from src.shared.python.biomechanics.multi_muscle import AntagonistPair as PyAntagonistPair
    
    # Python models
    py_flexors = PyMuscleGroup("Flexors")
    py_biceps_params = PyMuscleParameters(F_max=1000.0, l_opt=0.15, l_slack=0.20)
    py_flexors.add_muscle("biceps", PyHillMuscleModel(py_biceps_params), 0.04)
    
    py_extensors = PyMuscleGroup("Extensors")
    py_triceps_params = PyMuscleParameters(F_max=1200.0, l_opt=0.18, l_slack=0.22)
    py_extensors.add_muscle("triceps", PyHillMuscleModel(py_triceps_params), -0.035)
    
    py_elbow = PyAntagonistPair(py_flexors, py_extensors)
    
    # Rust models
    ru_flexors = upstream_muscle.MuscleGroup("Flexors")
    ru_biceps_params = upstream_muscle.MuscleParameters(1000.0, 0.15, 0.20, 10.0, 0.0, 0.05)
    ru_flexors.add_muscle("biceps", upstream_muscle.HillMuscleModel(ru_biceps_params), 0.04)
    
    ru_extensors = upstream_muscle.MuscleGroup("Extensors")
    ru_triceps_params = upstream_muscle.MuscleParameters(1200.0, 0.18, 0.22, 10.0, 0.0, 0.05)
    ru_extensors.add_muscle("triceps", upstream_muscle.HillMuscleModel(ru_triceps_params), -0.035)
    
    ru_elbow = upstream_muscle.AntagonistPair(ru_flexors, ru_extensors)
    
    flexor_act = {"biceps": 0.5}
    extensor_act = {"triceps": 0.2}
    states = {"biceps": (0.15, 0.0), "triceps": (0.18, 0.0)}
    
    py_torque = py_elbow.compute_net_torque(flexor_act, extensor_act, states)
    ru_torque = ru_elbow.compute_net_torque(flexor_act, extensor_act, states)
    
    np.testing.assert_allclose(py_torque, ru_torque, rtol=1e-5, atol=1e-8)
