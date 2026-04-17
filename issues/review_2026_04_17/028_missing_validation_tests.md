# [HIGH] Missing critical physics-validation tests

## Summary

The suite is missing end-to-end physics-validation tests that a
professional-grade product in this space is expected to pass. These
tests would pin down the bugs identified in issues #013 / #014 /
#015 / #016 and create the safety net for future refactors.

## Required tests (by priority)

### 1. Clubhead speed validation (HIGH)

End-to-end simulation from a prescribed joint-torque profile to
clubhead velocity at impact. Expected clubhead speed ranges (from
published PGA data):
- Driver: 70–80 m/s (155–180 mph)
- 7-iron: 35–40 m/s (78–90 mph)
- Wedge: 25–32 m/s (56–72 mph)

Tolerance: ±10 % vs. a canned reference swing per club.

### 2. Impact energy / momentum conservation (HIGH)

For a rigid-body impact model, `L_pre == L_post` (angular momentum)
and `E_pre - E_post = (1-COR²) · E_reduced_mass_kinetic`. See issue
#015 for the correct energy-loss formula.

Tolerance: `|ΔL| < 1e-4`, `|ΔE_predicted - ΔE_actual| / E_pre < 1e-3`.

### 3. Aerodynamic drag curve vs. empirical golf-ball Cd(Re) (HIGH)

Sweep Re ∈ `[1e4, 3e5]`, compare `DragModel.get_coefficient(v)` to
published Bearman–Harvey / Smits–Ogg data points. See issue #016.

Tolerance: ±15 % vs. reference; must reproduce the drag crisis
around Re ≈ 7e4.

### 4. Magnus / lift coefficient vs. empirical (HIGH)

Sweep spin ratio `S ∈ [0.05, 0.5]` at 30, 50, 70 m/s; compare to
published golf-ball Cl(S, Re) data.

### 5. TrackMan PGA-tour reference shot parity (HIGH)

Use `src/shared/python/validation_pkg/validation_data.py` PGA-tour
rows. For each club, back-solve the swing to match the reported
clubhead speed and spin, then forward-simulate and compare carry,
apex, landing angle.

Tolerance: carry ±5 %, apex ±10 %, landing angle ±2°.

### 6. URDF mass conservation under retargeting (MEDIUM)

Sum of link masses is invariant under retargeting operations that
scale the skeleton. Parametrize over multiple scale factors and
retargeting rules.

### 7. Swing-plane stability (MEDIUM)

Simulate a driven swing; fit a best-fit plane to the clubhead
trajectory in the downswing phase; the max normal-deviation over
the downswing is bounded to ±5 °. Per engine.

### 8. GRF vs. force-plate reference (MEDIUM)

Simulate a standard swing in each engine; compare vertical GRF
trace to a published force-plate reference (e.g., Han et al. 2019).
Peak ground-reaction force within ±15 %; centre-of-pressure
trajectory RMS within ±3 cm.

### 9. Sustained contact stability (MEDIUM)

Run a stationary humanoid for 10 seconds with feet in contact with
ground. Constraint residual must stay below 1 mm; joint-angle
drift must stay below 1° on unactuated joints.

### 10. Ballistic projectile closed-form parity (MEDIUM)

With aerodynamics disabled, projectile motion must match the exact
solution of `ẍ = 0, z̈ = -g` to machine precision.

### 11. Pendulum period vs. small-angle analytic (MEDIUM)

For a single and double pendulum with `θ0 < 0.1 rad`, simulated
period must match the linearized analytic period to 0.1 %.

### 12. Rotating-rigid-body Euler-equation check (MEDIUM)

Apply constant torque about non-principal axis, verify the
precession frequency matches `τ = I · ω̇`.

### 13. Contact KKT residual (MEDIUM)

Push the humanoid against a wall; verify `f_n ⊙ a_separation ≈ 0`
and `‖f_t‖ ≤ μ · f_n` across an entire step.

### 14. Sim2real gap instrumentation (MEDIUM)

Instrument the sim2real pipeline with a benchmark that captures
"delta between sim observation and real observation" as a
distribution. Does not need a real rig — captures the stack's
ability to represent that delta.

## Proposed structure

```
tests/
  physics_validation/
    test_clubhead_speed.py           # (1)
    test_impact_conservation.py      # (2), (13)
    test_aerodynamics_empirical.py   # (3), (4)
    test_trackman_parity.py          # (5)
    test_urdf_mass_conservation.py   # (6)
    test_swing_plane.py              # (7)
    test_grf_vs_forceplate.py        # (8)
    test_sustained_contact.py        # (9)
    test_closed_form_ballistic.py    # (10)
    test_pendulum_period.py          # (11)
    test_euler_rigid_body.py         # (12)
  sim2real/
    test_sim2real_gap_benchmark.py   # (14)
```

## Acceptance Criteria

- [ ] Each test listed above exists and runs on every engine where
      capability applies (gated via `capabilities.py`).
- [ ] Published references (Bearman-Harvey, Smits-Ogg, Han et al.,
      TrackMan tour data) are either vendored or cited with URLs in
      the test docstrings.
- [ ] Tests are in the `physics_validation` pytest marker and run
      on every PR.
- [ ] Each test has an explicit tolerance with a one-line derivation.

## Related

- Issue #013 — physics-convention bugs the tests would expose.
- Issue #014 — Pinocchio integration drift.
- Issue #015 — impact model correctness.
- Issue #016 — aerodynamics calibration.
- Issue #018 — missing golf-domain features this exercises end-to-end.
