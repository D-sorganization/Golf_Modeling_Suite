# [HIGH] Missing core golf-domain features — launch monitor, spin loft, attack angle, shaft lean, swing-fault diagnosis

## Summary

The suite positions itself as "professional-grade" for golf modeling.
Measured against any commercial reference (TrackMan, FlightScope,
Foresight), a number of foundational domain features are simply absent.
These are not polish — they are the vocabulary of the sport. Without
them the product cannot be pitched to coaches, fitters, or sports
scientists.

## Missing features

Each bullet includes the minimum scope for a first cut:

### 1. Launch-monitor ingestion API

There is no module that ingests a TrackMan / FlightScope / Foresight
CSV/JSON dump and maps it to internal `PreImpactState` / `BallFlight`
types. Implication: no calibration, no inverse-modeling, no comparison
against real shots.

**Proposal:** `src/shared/python/launch_monitor/` with adapters
(`trackman.py`, `flightscope.py`, `foresight.py`) that return a
normalized `LaunchMonitorShot` dataclass.

### 2. Spin-axis / spin-loft decomposition

`src/shared/python/physics/impact_model/` computes a 3-D spin vector
but never decomposes it into spin-loft (perpendicular spin w.r.t.
velocity) and spin-axis tilt (heel-toe curvature). These are the
standard coaching metrics.

**Proposal:** `decompose_spin(v_ball, omega_ball)` -> `{backspin_rpm,
sidespin_rpm, spin_axis_deg, spin_loft_deg}`.

### 3. Attack angle and dynamic loft

There is nowhere in the code that computes attack angle (velocity
direction vs. ground plane) at impact. Static `clubhead_loft` is
used in `PreImpactState`, but dynamic loft = static loft − shaft lean +
attack angle. All three must be computed from swing kinematics at the
impact frame.

**Proposal:** `compute_impact_geometry(swing_trajectory, impact_frame)`
-> `{attack_angle_deg, dynamic_loft_deg, shaft_lean_deg, club_path_deg,
face_angle_deg, face_to_path_deg}`.

### 4. Shaft-lean modeling

Shaft lean at impact governs ~half the variance in dynamic loft.
The generated URDF treats shaft and head as rigid (see issue #019),
so shaft lean cannot be observed even if we want to. A `ShaftLeanSensor`
module that reads hand frame + head frame at impact and reports the
angle in the swing plane is the minimum.

### 5. Ground-reaction-force (GRF) validation against force-plate data

`src/shared/python/physics/ground_reaction_forces.py` exists but is
never populated by the simulation engines. No test compares simulated
GRF to published force-plate traces (e.g., Han et al. 2019; Peterson
et al. 2016).

**Proposal:** add a reference trace under
`src/shared/python/validation_pkg/forceplate_reference/`; add a
parametric test that simulates a swing and compares peak vertical GRF
and centre-of-pressure trajectory to the reference.

### 6. Club-fitting workflow

Shaft flex (Regular / Stiff / Extra Stiff), shaft length, lie angle,
loft, and head weight are fittable parameters. The suite has
data structures for them but no `recommend_fit(swing_speed, tempo,
attack_angle) -> ClubSpec` workflow.

### 7. Swing-fault diagnosis

Coaches look for: early extension, casting, lag loss, over-the-top,
sway/slide, reverse pivot. The suite's biomechanical analysis
(`src/shared/python/biomechanics/`, `src/shared/python/injury/`) has
no swing-fault detector that translates joint-angle time series into
diagnostic strings.

**Proposal:** `src/shared/python/swing_analysis/fault_detector.py`
with registered rules; outputs structured `[{"fault": "casting",
"severity": 0.7, "evidence": {...}}]`.

### 8. Putting-specific model gap

`src/engines/physics_engines/putting_green/python/` exists but the
ball-roll physics (`ball_roll_physics.py`) uses a constant friction
coefficient; no Stimpmeter calibration, no slope-induced break, no
grain effect, no initial-skid-to-roll transition.

### 9. Multi-ball trajectory comparison / shot-pattern statistics

There is no module that simulates N shots with stochastic swing
variation and produces a dispersion pattern (smash factor distribution,
90 % carry ellipse, consistency metrics). This is trivial once (1)-(4)
are in place.

### 10. Units and conventions are inconsistent across the stack

`src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/cli_runner.py`
hard-codes `2.23694` (m/s→mph) inline without referencing the shared
constant. `src/shared/python/club_data/loader.py` accepts mph and m/s
interchangeably with no unit-tag. Without a unit contract, every
integration is fragile.

**Proposal:** adopt `pint` or `astropy.units` on the public API
boundary (LaunchMonitorShot, ClubSpec, BallFlight) and convert to SI
internally.

## Impact

Without these, the suite cannot be used by any target persona:
coaches (need swing-fault diagnosis), fitters (need club-fit workflow),
scientists (need GRF/launch-monitor parity), or equipment R&D (need
dispersion patterns).

## Acceptance Criteria

- [ ] Launch-monitor ingestion API lands with adapters for TrackMan
      and FlightScope and at least one end-to-end test.
- [ ] `decompose_spin()` + `compute_impact_geometry()` functions
      with unit tests against published measurements.
- [ ] GRF validation test against at least one published force-plate
      trace.
- [ ] Swing-fault detector with at least five rules and test
      vectors for each.
- [ ] `pint`-based units contract on public types; deprecation
      warning for raw-float callers.

## Related

- Issue #015 — impact model that these features build on.
- Issue #016 — aerodynamics.
- Issue #017 — humanoid URDF fidelity.
- Issue #019 — shaft / club model.
