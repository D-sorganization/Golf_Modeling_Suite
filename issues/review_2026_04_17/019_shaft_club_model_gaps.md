# [HIGH] Shaft / club model gaps: no torsion, static loft, unused equipment specs, fixed grip friction

## Summary

The club model is the link between humanoid control and ball flight. A
number of defects and missing features in the shaft, head, and grip
models mean the suite cannot meaningfully simulate shaft-flex
sensitivity or face-angle control — two of the most-studied effects in
golf equipment research.

## Findings

### 1. No torsional shaft dynamics

`src/shared/python/physics/flexible_shaft.py:1-22` — module docstring
states explicitly:

> Euler–Bernoulli beam model ignores torsional twisting.

Torsion is critical for face-angle control: driver torque (in °/100
lb-in) is spec'd by every manufacturer because torsional twist
happens during the downswing and changes face angle at impact.
Current code cannot simulate, fit, or rank shafts on torque.

**Fix:** add a Saint-Venant torsion term with polar moment of inertia
`J = β·b·t³` (circular shaft). Couple to head yaw via an inertial
constraint.

### 2. Shaft bending uses only the first bending mode

Even the bending side uses a single modal DOF. For a 45" driver,
3+ modes are needed to represent loading, release, and lead-release
dynamics in the downswing accurately.

### 3. Shaft flex stiffness is not coupled to tempo / swing-speed in `recommend` APIs

There is no club-fitting function that takes swing speed, tempo, and
release point and returns a recommended flex (Regular/Stiff/X-Stiff).
The data model has flex enums; no decision logic uses them.

### 4. Grip-friction coefficient is constant

`src/shared/python/physics/grip_contact_model.py:1-100` uses a default
`STATIC_FRICTION = 0.8` for "rubber grip on dry skin" with no slip-
velocity dependence, no humidity model, and no degradation to ~0.3
for wet grips. Grip slip at the top of the swing is a real failure
mode and cannot be simulated.

### 5. Static clubhead loft is used regardless of swing kinematics

`src/shared/python/physics/impact_model/models.py` reads
`clubhead_loft` from `PreImpactState`, which is whatever the swing
model wrote there. There is no code path that computes dynamic loft
from velocity + shaft lean at the impact frame.

### 6. Shaft length constants are USGA legal maximums, not tour averages

`src/shared/python/physics/flexible_shaft.py:47-54`:
`1.168 m` driver (46"), `0.965 m` iron (38"). Tour averages are
`1.155 m` (45.5") and `0.940 m` (37") for 7-iron. The difference
shifts effective moment of inertia and impact offset.

### 7. Clubhead moment of inertia is a scalar, not a 3×3 tensor

`_compute_effective_club_mass` takes a scalar `I_club`. A modern
driver has ~5500 g·cm² MOI about the vertical and ~3500 g·cm² about
horizontal — the anisotropy is a primary design variable. See the
impact-model issue (#015) for the coupling.

### 8. `src/shared/python/physics/equipment.py` is referenced but unused in the hot path

Equipment module defines club specs (loft, lie, length, head mass,
MOI) but the impact model does not read from it; it reads only from
`PreImpactState` fields populated by the swing model. Specs vs.
simulation drift silently.

### 9. Unit handling on `smash_factor` is fragile

`src/shared/python/club_data/loader.py` reads mph and m/s columns
interchangeably based on column name. A miscast produces a smash
factor off by `3.6` (factor of ~8 error), with no validation.

## Impact

Club-fitting, shaft-flex experiments, and face-angle control studies
cannot be done with the current model. This is a large block of
research that the suite is marketed toward.

## Acceptance Criteria

- [ ] Implement shaft torsion in `flexible_shaft.py` with a test that
      reproduces a 4 °/kg·m torque coefficient at static load.
- [ ] Extend the bending model to at least 3 modes; add a
      frequency-response test against published shaft-flex data.
- [ ] Add `recommend_shaft_flex(swing_speed_mph, tempo_ms,
      release_timing_ms) -> FlexCategory` with rule-based logic.
- [ ] Replace constant grip friction with a slip-velocity-dependent
      model and a humidity factor; add a grip-slip unit test.
- [ ] Compute dynamic loft from impact-frame kinematics and use it
      in `ImpactModel.solve()`.
- [ ] Move hard-coded shaft lengths into `equipment.py` and allow
      per-club overrides; use tour averages as defaults.
- [ ] Change `I_club` to a full inertia tensor; exercise the toe/heel
      strike asymmetry in a unit test.
- [ ] Make `ImpactModel.solve()` read from `ClubSpec` rather than from
      dangling `PreImpactState` fields; deprecate the raw fields.
- [ ] Unit-tag the columns in `club_data/loader.py` and raise on
      ambiguous input.

## Related

- Issue #015 — impact model.
- Issue #017 — humanoid URDF (shaft attached to both hands).
- Issue #018 — missing club-fit workflow and launch-monitor ingestion.
