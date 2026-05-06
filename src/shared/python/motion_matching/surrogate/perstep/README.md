# Per-step dynamics surrogate

Per-step variant of the Option 2 forward surrogate. Lives side-by-side with the
trajectory-level surrogate in the parent package
(`src/shared/python/motion_matching/surrogate/`). Both are valid Option 2
instantiations; the choice depends on what your dataset and inversion budget
look like.

## Mapping

```
f_theta : (q, q_dot, tau) -> (q, q_dot, q_ddot)
```

A small MLP regresses next-step kinematics from the current state and the
applied torques. Originally landed in PR #3966 under
`MachineLearning/train_dynamics_surrogate.py`; relocated here in issue #4044.

## When to use this vs the trajectory-level surrogate

| Aspect | Per-step (this package) | Trajectory-level (parent package) |
|---|---|---|
| Mapping | `(q, q_dot, tau) -> (q, q_dot, q_ddot)` | `theta_coeffs -> kinematics(t)` |
| Decision-space cardinality at inversion | `N x n_controls` | `7 x n_joints` |
| Inversion algorithm | Adam-on-grid (this package's `optimize.py`) | Differentiable end-to-end (parent `invert.py`) |
| Temporal context | None — frames are i.i.d. | Whole swing, conditioned on coefficients |
| Training data shape | Independent rows of `(q, q_dot, tau, q_ddot)` | Whole swings indexed by `trial_id` |
| Training cost | Cheaper (smaller model, no FiLM, no time embed) | Higher (FiLM-MLP at fixed `N=300`) |
| Coefficient output | Post-fit polyfit via `export_torque_polynomials.py` | Direct decision variable |

Use **per-step** when:

- The parquet dataset has independent `(q, q_dot, tau) -> (q, q_dot, q_ddot)` rows.
- You want fast training and don't need temporal coherence in the surrogate.
- You're happy to recover polynomial coefficients via post-fit `polyfit` after
  Adam-on-grid converges (see `export_torque_polynomials.py`).

Use **trajectory-level** when:

- The dataset has whole swings (one row per `trial_id` with `N=300` timesteps).
- You want a single forward pass to map a coefficient vector to a kinematic
  trajectory, and a single backward pass to invert.
- Temporal coherence (smooth velocities, no per-frame jitter) matters at
  inversion time.

Both can produce polynomial coefficients in the end; the per-step path runs
`export_torque_polynomials.py` after Adam converges, while the trajectory-level
path is parameterised by coefficients from the start.

## Public API

```python
from src.shared.python.motion_matching.surrogate.perstep import (
    DynamicsMLP,
    TrainConfig,
    train_dynamics_surrogate,
    optimize_torque_sequence,
    extract_dataset,
)
```

The old import paths under `MachineLearning/` continue to work as thin shims
that emit a `DeprecationWarning` on import. They will be removed once all
callers migrate.
