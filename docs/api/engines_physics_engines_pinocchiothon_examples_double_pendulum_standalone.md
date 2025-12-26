# engines.physics_engines.pinocchiothon.examples.double_pendulum_standalone

double_pendulum.py

Planar double pendulum model with:

- Dynamics: x_dot = f(x, u)
- Natural torque field: tau_nat(q, qdot, qddot)
- Example PD input and simulation
- Optional end-effector wrench reconstruction

State vector:
    x = [q1, q2, q1dot, q2dot]

This file is intended as a standalone module that you can
import into a Streamlit app or run directly.

## Constants

- `I1`
- `I2`
- `N`
- `J`
