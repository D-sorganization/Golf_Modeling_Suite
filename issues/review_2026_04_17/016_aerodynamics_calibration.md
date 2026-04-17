# [HIGH] Aerodynamics model is not empirically calibrated and under-specifies the drag crisis

## Summary

Golf ball aerodynamics (`src/shared/python/physics/aerodynamics.py`,
`src/shared/python/physics/ball_flight_physics.py`,
`src/engines/common/physics.py`) is a first-order sketch: constant-value
Cd/Cl/Cm, linear Re interpolation, hard-coded polynomial coefficients
with no source citation, and a `WindModel` class that is wired into
`AerodynamicsEngine.compute_forces()` but ignored by the calculator
actually used by the trajectory simulator. This is not good enough for
a simulator that aspires to match launch-monitor reality.

## Findings

### 1. Drag-crisis model is piecewise-linear, not empirical

`src/engines/common/physics.py:302-310` and
`src/shared/python/physics/aerodynamics.py:258-298`

Cd is a 3-segment piecewise-linear function of Re with breakpoints
at 8e4 and 2e5, laminar Cd = 0.5, turbulent Cd = user-provided
(`GOLF_BALL_DRAG_COEFFICIENT`, default ~0.25). Real dimpled-ball Cd
exhibits a *minimum* around Re ≈ 7e4 (not a monotone drop), and the
post-crisis Cd is speed-dependent, not constant. Use the Bearman–Harvey
or Smits & Ogg empirical curves (coefficients table, not a formula) and
interpolate with a natural cubic spline. Add a citation to the
docstring.

### 2. Lift coefficient is a 2nd-order polynomial in spin-ratio with unsourced coefficients

`src/shared/python/physics/ball_flight_physics.py:78-85`

`Cl = cl0 + s·(cl1 + s·cl2)` with `cl0=0.00, cl1=0.38, cl2=0.08`. No
reference is given for these numbers. The saturation at
`Cl_max = 0.4` in `src/shared/python/physics/aerodynamics.py:388-391`
is an arbitrary cap that silences tuning errors. Replace with the
Smits–Ogg empirical fit `Cl = f(S, Re)` and add a parametrized unit test
across realistic `S ∈ [0.05, 0.5], v ∈ [30, 80] m/s`.

### 3. Magnus coefficient is a linear cap with no Re dependence

`src/engines/common/physics.py:329-343`: `Cm = 0.4 · min(S, 0.5)`.

Missing: Re dependence, Robins-effect threshold, decoupling of
backspin (vertical-axis) vs. sidespin (horizontal-axis) Magnus
contributions. The current formula couples everything through the
spin scalar `S`, which means a ball with pure sidespin produces the
same Magnus coefficient as one with pure backspin.

### 4. `WindModel` exists but is decorative

`src/shared/python/physics/aerodynamics.py:132-187` implements a
full `WindModel` (mean + gust + turbulence), but the `compute_forces`
entry point that the trajectory simulator actually calls does not
read it. Wind has zero effect on any existing trajectory in the test
suite.

### 5. No air-density altitude model is wired in

`AirProperties.from_altitude()` exists but is not threaded through
`BallFlightSimulator`. Shots in Denver vs. sea level compute with
identical `ρ = 1.225 kg/m³`, which is ~15 % wrong at altitude.

### 6. Spin decay is a single time constant, independent of velocity

`SPIN_DECAY_RATE_S` is a global constant. In reality `τ_spin ∝ 1/|v|`
for viscous damping. A 60 m/s drive and a 25 m/s wedge decay at the
same rate in the current model.

### 7. Validation data is committed but unused

`src/shared/python/validation_pkg/validation_data.py:90-150` contains
PGA Tour TrackMan reference shots. No test in the suite runs the
ball-flight simulator and compares carry, apex, and landing angle to
those references.

## Impact

Carry distance, apex, spin decay, wind drift, and altitude sensitivity
are all systematically wrong. The TrackMan reference data that was
committed for validation is dead code.

## Reproduction

```python
# 1. Simulate 90 mph clubhead, 15° launch, 2500 rpm backspin at sea level.
# 2. Expect carry ~ 250 yd (TrackMan PGA average for 7-iron... I mean driver).
# 3. Re-run at Denver (ρ = 1.06 kg/m³); expect ~10 yd more carry.
# 4. Compare to validation_data.py reference rows.
```

None of these steps run in the current test suite.

## Acceptance Criteria

- [ ] Replace piecewise-linear Cd(Re) with a cubic spline fit of
      published golf-ball Cd data; commit the source data under
      `src/shared/python/physics/calibration_data/`.
- [ ] Replace hard-coded Cl polynomial with the Smits–Ogg empirical fit;
      cite in docstring.
- [ ] Add Re dependence to Magnus; decouple backspin and sidespin axes.
- [ ] Wire `WindModel` into `AerodynamicsEngine.compute_forces()` and
      add a wind-drift regression test.
- [ ] Thread `AirProperties.from_altitude(altitude_m)` through
      `BallFlightSimulator`; add a Denver-vs-sea-level carry test.
- [ ] Make spin-decay time constant velocity-dependent; add a unit
      test of spin loss over 5 s at 70 m/s vs. 25 m/s.
- [ ] Port `validation_data.py` reference shots into a parametrized
      `tests/physics_validation/test_ball_flight_trackman_parity.py`
      with per-club carry-distance tolerance bands.
- [ ] Remove the `Cl_max = 0.4` clamp unless it is justified by a
      cited reference.

## Related

- Issue #015 — impact model feeding this.
- Issue #028 — missing trajectory validation tests.
