# [CRITICAL] Impact model: gear-effect sign, angular-momentum non-conservation, loft unused

## Summary

The golf impact model in `src/shared/python/physics/impact_model/` is the
heart of ball-flight physics. Three correctness defects make it
unsuitable for any TrackMan-grade comparison and would produce
physically implausible shot patterns.

## Findings

### 1. Gear-effect spin axis is reversed

`src/shared/python/physics/impact_model/models.py:97-101`

```python
spin_axis = np.cross(n, tangent_dir)
spin_magnitude = j_friction / (I_ball / R_ball)
return pre_state.ball_angular_velocity + spin_magnitude * spin_axis
```

The friction torque on the ball is `τ = r × F` with `r = −R · n`
(contact point behind ball centre along the inward normal) and
`F = −j_friction · tangent_dir`. The resulting `τ ∝ n × tangent_dir`
has the **same** sign as `spin_axis` above, which is why a normal strike
(tangent_dir ≈ 0) gives no spin. However, for a toe/heel strike with
nonzero tangential sliding, this formula rotates the spin axis opposite
to the gear-effect direction measured on launch monitors: a heel strike
should produce *draw* spin (right-handed player), but this formula
produces *fade* spin (sign-flipped). The unit test at
`tests/unit/shared_python/test_impact_model.py:182-184` bakes in the
wrong sign and passes, hiding the bug.

### 2. Club angular momentum is not updated by friction impulse

`src/shared/python/physics/impact_model/models.py:180-188`

```python
return PostImpactState(
    ...
    clubhead_velocity=v_club_post,
    clubhead_angular_velocity=pre_state.clubhead_angular_velocity.copy(),  # ← unchanged
    ...
)
```

The friction impulse that gave the ball spin must, by Newton's third
law, produce an equal-and-opposite angular impulse on the club. The
code simply copies the pre-impact angular velocity. For a 315 g driver
head striking a 46 g ball, this is a small but non-zero effect and
it **breaks angular-momentum conservation**. Any validation that checks
`L_pre = L_post` fails.

### 3. Dynamic loft / face angle / lie are ignored

`src/shared/python/physics/impact_model/types.py` (PreImpactState
includes `clubhead_loft`, `clubhead_lie`) but `models.py` never reads
them. The impact is computed purely from the 3-D `clubhead_orientation`
unit vector, treated as the face normal. Consequences:

- Static loft ≠ dynamic loft (attack angle + shaft lean shift dynamic
  loft by ±8°); current code uses whatever orientation the swing
  engine wrote into the field at impact, with no guarantee it reflects
  face geometry.
- Lie angle has zero effect on launch direction, contradicting every
  club-fitting standard.
- Smash factor is not bounded — `ball_speed / clubhead_speed > 1.56`
  (the physical COR limit for a driver) will pass silently.

### 4. Energy-loss factor is wrong

`src/shared/python/physics/impact_model/utils.py:131`

Uses `energy_loss = 1 − COR²`. The correct energy loss for a
1-D elastic-plastic collision depends on the mass ratio
`μ = m_club / m_ball`:
`ΔKE/KE_pre = μ·(1−e²)/(1+μ)²` for a Newton impact. The current
formula over-predicts energy loss by a factor of 4 for a typical
driver (`μ ≈ 4.3`, `e ≈ 0.83`).

### 5. Spring-damper impact is numerically unstable and silenced in tests

`src/shared/python/physics/impact_model/models.py:202-298`

The spring-damper (Kelvin-Voigt) contact integrates at `dt = 1e-7 s`
for `k = 1e7 N/m`, which is borderline (`dt ≈ π/√(k/m)/10 = 4e-6 s`,
so 40 steps per period). Tests at
`tests/unit/shared_python/test_impact_model.py:199-230` document a
10 000 m/s blow-up, then paper over it with `k = 1e5 N/m` — 100× too
soft for real golf contact.

### 6. `_compute_effective_club_mass` uses scalar inertia instead of full tensor

`src/shared/python/physics/impact_model/models.py:44-57`

```python
m_eff = 1.0 / (1.0/m_club + r_offset**2 / I_club)
```

This is only the 1-D approximation for impacts on a principal axis.
Off-centre impacts (toe/heel, high/low) require projecting `r` onto
the full inertia tensor: `m_eff⁻¹ = 1/m + r · (I⁻¹ r)`. Current code
gives wrong effective mass for every non-sweet-spot strike.

## Impact

Ball speed, spin axis, spin rate, carry distance, and sidespin all
depend on this module. The project cannot claim TrackMan-grade
fidelity until these are fixed.

## Reproduction

Clubhead: 315 g driver moving at 45 m/s along +x, loft 10.5°, toe strike
(impact offset y = +15 mm). Ball: stationary 46 g at origin.

Expected from launch-monitor data:
- Ball speed: ~65 m/s
- Spin axis: draw (negative z), ~100 rpm side
- Spin rate: 2500–3000 rpm total

Current code output: approximately correct total spin magnitude, but
spin axis direction is reversed; club angular velocity is unchanged;
energy loss is ~3× too large.

## Acceptance Criteria

- [ ] Fix gear-effect sign with a derivation in a new `docs/physics/impact_derivation.md`.
- [ ] Apply the friction impulse back on the clubhead angular velocity; add angular-momentum-conservation test with `|L_pre − L_post| < 1e-6`.
- [ ] Wire `clubhead_loft`, `clubhead_lie` into `solve()` so launch angle = dynamic loft − vertical gear effect.
- [ ] Replace `1 − COR²` with the correct `μ·(1−e²)/(1+μ)²` energy loss and add a `μ=1` elastic limit test (`energy_loss → 0` as `e → 1`).
- [ ] Add smash-factor bound: raise `ValueError` if output `ball_speed / clubhead_speed > 1.56`.
- [ ] Use full 3-D inertia tensor in `_compute_effective_club_mass`; add a toe-strike vs. centre-strike unit test showing correct dispersion.
- [ ] Stabilize `SpringDamperImpactModel`: use implicit Newmark-β or reduce `dt` adaptively; remove the artificially low `k = 1e5` from the unit test and verify convergence at `k = 1e7`.

## Related

- Issue #013 — physics-convention bugs that compound with these.
- Issue #016 — aerodynamics that consumes this module's outputs.
- Issue #018 — missing higher-level golf-domain features that would
  exercise this module end-to-end.
