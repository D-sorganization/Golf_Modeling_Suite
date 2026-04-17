# [HIGH] Humanoid URDF models are toy-grade; grip is asymmetric and joints are missing

## Summary

The suite advertises itself as a humanoid-golf modeling platform, but
the shipped URDFs are far below research-grade biomechanical fidelity.
The "simple" humanoid has no elbows, knees, wrists, or fingers; the
detailed "golfer" URDF attaches the club only to the left hand; and
inertias across all models are hand-tuned instead of derived from
published anthropometry.

## Findings

### 1. `simple_humanoid.urdf` has 5 revolute joints total

`src/shared/urdf/simple_humanoid.urdf` — neck, 2 shoulders, 2 hips; no
elbows, knees, wrists, ankles, spine, pelvis. This cannot represent
any golf swing biomechanics. If this file is used only for smoke tests
it should be renamed (e.g. `smoke_test_humanoid.urdf`) and kept out of
model-discovery paths; if it is ever loaded for physics work, replace
it.

### 2. `golfer.urdf` grip is asymmetric — only the left hand holds the club

`src/engines/physics_engines/pinocchio/models/generated/golfer.urdf`

```xml
<joint name="hand_left_to_club_shaft" type="fixed">
  <child link="club_shaft"/>
```

No corresponding `hand_right_to_club_shaft` joint. Real golfers use
both hands. The kinematic chain implies that right-hand motion has no
direct mechanical influence on the club — which is false and which
will bias every torque/force analysis. Options: add a 6-DoF bushing
joint from the right hand to the club (or to the left hand); or use
a closed-loop constraint with an explicit constraint solver.

### 3. Club shaft is rigid (`type="fixed"` to head)

The `club_shaft_to_club_head` joint is `fixed`, and there is no
flex model. Issue #019 covers the shaft-flex problem in detail.

### 4. Inertias are hand-tuned constants

`simple_humanoid.urdf`: torso `mass=10`, `ixx=iyy=0.4, izz=0.2`; head
`mass=2, ixx=iyy=izz=0.02`. These are round numbers, not values
derived from a published dataset (Winter 2009; de Leva 1996; Dempster
1955). Retargeting workflows in `src/learning/retargeting/` cannot
preserve mass properties if the source has no physiological grounding.

### 5. No finger joints — grip compliance is impossible to model

Neither URDF models fingers individually. Grip force, grip slip, and
hand-orientation-dependent loft adjustments cannot be captured.

### 6. No joint limits documented in anatomical ranges

The generated golfer URDF contains `<limit>` tags with numeric values
but no reference to ROM literature. Shoulder ROM is highly
sport-specific (golf uses >180° external rotation at top-of-swing);
the defaults likely clamp a realistic swing.

### 7. MuJoCo humanoid model only `simple_pendulum.xml` is shipped

`src/engines/physics_engines/mujoco/models/` contains only
`simple_pendulum.xml` and `__init__.py`. The golf-swing MuJoCo models
referenced in `src/engines/physics_engines/mujoco/python/golf_swing_models_xml.py`
are generated programmatically; there is no static reference MJCF the
team can eyeball-verify.

## Impact

Any biomechanical claim the project makes (joint stress, injury risk,
ground-reaction forces, swing-plane validation) is built on a model
that does not have enough DOFs to produce the claimed effects.

## Acceptance Criteria

- [ ] Replace `simple_humanoid.urdf` with a full-body URDF that
      includes at minimum: 3-DOF neck, 3-DOF shoulder × 2, 1-DOF
      elbow × 2, 3-DOF wrist × 2, 6-DOF spine (segmented),
      6-DOF pelvis, 3-DOF hip × 2, 1-DOF knee × 2, 2-DOF ankle × 2.
- [ ] Derive link masses and inertias from a cited anthropometry
      dataset (de Leva 1996 regression coefficients are
      recommended) parameterized by subject height and mass.
- [ ] Add a right-hand grip to `golfer.urdf`. Either a duplicate
      `fixed` joint (and then enforce mass-property consistency)
      or a bushing joint with stiffness/damping derived from a
      grip-force model.
- [ ] Add per-finger joints or at minimum a `grip_compliance`
      6-DoF joint between each hand and the club.
- [ ] Document shoulder / wrist / hip ROM in a YAML sidecar that
      references published golf-biomechanics literature (Cheetham,
      Hume, etc.).
- [ ] Commit a static `humanoid_golfer.xml` MJCF as the MuJoCo
      counterpart; regenerate the Pinocchio URDF from the same
      source of truth.
- [ ] Add a URDF mass-conservation test: total robot mass equals
      sum of links, unchanged after retargeting.

## Related

- Issue #019 — shaft / club modeling.
- Issue #018 — missing golf-domain features that need this fidelity.
- Issue #028 — missing URDF-mass conservation tests.
