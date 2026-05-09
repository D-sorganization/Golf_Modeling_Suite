# Leg-Chain Design Notes — 3D_FullBody_Model

This file is the design surface for `add_leg_chain.m`. It exists so
the agent / human filling in the actual `add_block` calls has a
single-page reference for what each block is, what it connects to,
and what mask parameters to set.

Current status: first left-leg implementation slice. `add_leg_chain.m`
now deletes and rebuilds a generated `Left Leg Kinetically Driven`
subsystem with the hip, knee, ankle, foot, and ball-of-foot anchor
blocks listed below. The right-side mirror and full sphere-plane contact
wiring are deliberately deferred. Simscape-library operations that vary
by MATLAB release/license are recorded in the returned operation log
instead of being treated as silent success.

## Body chain

```
                 ┌─────── Pelvis (existing) ───────┐
                 │                                 │
                 ▼                                 ▼
         L Hip Gimbal                       R Hip Gimbal
            (3 DOF)                           (3 DOF)
                 │                                 │
                 ▼                                 ▼
            L Upper Leg                       R Upper Leg
         (Cylindrical Solid,                (Cylindrical Solid,
          length=UpperLegLength)            length=UpperLegLength)
                 │                                 │
                 ▼                                 ▼
          L Knee Revolute                    R Knee Revolute
            (1 DOF)                           (1 DOF)
                 │                                 │
                 ▼                                 ▼
            L Lower Leg                       R Lower Leg
                 │                                 │
                 ▼                                 ▼
         L Ankle Universal                  R Ankle Universal
            (2 DOF)                           (2 DOF)
                 │                                 │
                 ▼                                 ▼
              L Foot                            R Foot
         (Brick Solid +                    (Brick Solid +
          BallOfFoot Sphere)                BallOfFoot Sphere)
                 │                                 │
                 └────► Spatial Contact Force ◄───┘
                        (each foot vs. World ground plane)
```

## Block list with library paths

Library paths are documented as Simulink browse paths so they can be
used by `add_block(<src>, <dst>)` calls.

### Joints

| Joint                 | Library path                    | DOF                | Mask params (per axis)                                                                                 |
| --------------------- | ------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------ |
| Hip Gimbal (L/R)      | `sm_lib/Joints/Gimbal Joint`    | X / Y / Z revolute | `{X,Y,Z}PositionTargetSpecify`, `{X,Y,Z}MotionActuationMode`, `{X,Y,Z}TorqueActuationMode`             |
| Knee Revolute (L/R)   | `sm_lib/Joints/Revolute Joint`  | Z revolute         | `PositionTargetSpecify=user`, `MotionActuationMode=automatic`, `TorqueActuationMode=provided by input` |
| Ankle Universal (L/R) | `sm_lib/Joints/Universal Joint` | X / Y revolute     | same convention as Gimbal but two axes                                                                 |

For the kinetically-driven mechanics (damping, polynomial torque), the
existing models in
`3D_Golf_Model/matlab/src/model/{Kinetically_Driven_Gimbal,Revolute,Universal}_Joint.slx`
are libraries — **reuse them** rather than reinventing the controller
internals. Pattern: drag the corresponding library reference into the
new leg subsystem; connect its conserving frame ports to the
upper/lower segments. The current slice creates the stable subsystem,
port, joint, body, and reporting surface first; replacing any fallback
release-specific wiring with direct library-reference mechanics remains
follow-up work.

### Rigid bodies

| Body                                | Library path                             | Mask params                                                                           |
| ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------- |
| Upper Leg / Lower Leg (cylindrical) | `sm_lib/Body Elements/Cylindrical Solid` | `CylinderRadius=UpperLegRadius`, `CylinderLength=UpperLegLength`, `Mass=UpperLegMass` |
| Foot (rectangular)                  | `sm_lib/Body Elements/Brick Solid`       | `BrickDimensions=[FootLength, FootWidth, FootHeight]`, `Mass=FootMass`                |
| Ball of foot (contact sphere)       | `sm_lib/Body Elements/Spherical Solid`   | `SphereRadius=0.03`, parented to the foot's toe end via Rigid Transform               |

### Contact

| Block             | Library path                                      | Mask params                                                                                                                                                                                                                                                        |
| ----------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Ground plane      | `sm_lib/Body Elements/Infinite Plane`             | parented to World Frame at z=0, normal=+Z                                                                                                                                                                                                                          |
| Foot contact (×2) | `sm_lib/Forces and Torques/Spatial Contact Force` | `Geometry: Sphere/Plane`, sphere radius = 0.03, plane = ground. `NormalForce: Stiffness and Damping`, `K=GroundContactStiffness`, `D=GroundContactDamping`, friction model = Smooth Stick-Slip with `static=GroundFrictionStatic`, `kinetic=GroundFrictionKinetic` |

### Sensors (logged signals — minimised to stay within budget)

| Sensor                                  | What it produces                           | Justification                                                                       |
| --------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------- |
| Transform Sensor on each joint          | rotation matrix + angular position scalars | Same as existing arm/spine joints — read by `extractAllSignalsFromBus`              |
| Inertia Sensor on lower leg + foot only | global position + acceleration             | Need foot trajectory for contact analysis; upper-leg landmark is computable from FK |

## Polynomial-torque parameter naming

For `getPolynomialParameterInfo()` to discover the new joints, each
joint's torque must be driven by 7 polynomial coefficients named with
the convention `<JointName><Axis><A..G>`. We use:

| Joint    | Coefficient names                                              |
| -------- | -------------------------------------------------------------- |
| LHip X   | `LHipXA` `LHipXB` `LHipXC` `LHipXD` `LHipXE` `LHipXF` `LHipXG` |
| LHip Y   | `LHipYA` … `LHipYG`                                            |
| LHip Z   | `LHipZA` … `LHipZG`                                            |
| LKnee    | `LKneeA` … `LKneeG`                                            |
| LAnkle X | `LAnkleXA` … `LAnkleXG`                                        |
| LAnkle Y | `LAnkleYA` … `LAnkleYG`                                        |

| (RHip, RKnee, RAnkle equivalents)

Total new joints: **6 axes per side × 2 sides = 12 new joint families**
× 7 coefficients = **84 new polynomial coefficients** added to the
`PolynomialInputValues.mat` file.

Result: the `theta` vector grows from `27 * 7 = 189` to `39 * 7 = 273`
elements automatically. This resolves the earlier 33-vs-39 ambiguity:
the discovery helper counts each hip and ankle axis as a separate
coefficient family, not each anatomical joint as one family. The
matcher's `theta_to_polynomial_struct` helper handles arbitrary joint
counts already, but optimizer entry points must validate against the
model-family-specific expected length before running.

## Start-position parameter naming

Following the existing convention for arms (e.g.
`LSStartPositionX/Y/Z`, `LEStartPosition`):

| Joint   | Variables                                          |
| ------- | -------------------------------------------------- |
| L Hip   | `LHipStartPositionX/Y/Z`, `LHipStartVelocityX/Y/Z` |
| R Hip   | `RHipStartPositionX/Y/Z`, `RHipStartVelocityX/Y/Z` |
| L Knee  | `LKneeStartPosition`, `LKneeStartVelocity`         |
| R Knee  | `RKneeStartPosition`, `RKneeStartVelocity`         |
| L Ankle | `LAnkleStartPositionX/Y`, `LAnkleStartVelocityX/Y` |
| R Ankle | `RAnkleStartPositionX/Y`, `RAnkleStartVelocityX/Y` |

These are added to the model-workspace by `add_leg_chain.m`'s
`local_default_workspace_vars` helper. At a neutral standing pose
they're all zero; the matcher's "Address" reference golfer will need
small values for knee flex (`LKneeStartPosition = 8.0`,
`RKneeStartPosition = 8.0`) and hip-X tilt (`LHipStartPositionX =
-15.0`, mirroring the spine forward tilt).

## Block budget breakdown (target)

| Component                                                      | Blocks (estimate) |
| -------------------------------------------------------------- | ----------------: |
| Hip Gimbal (×2)                                                |                16 |
| Knee Revolute (×2)                                             |                 6 |
| Ankle Universal (×2)                                           |                12 |
| Upper Leg (×2)                                                 |                 6 |
| Lower Leg (×2)                                                 |                 6 |
| Foot Brick + BallOfFoot Sphere (×2)                            |                12 |
| Ground Plane                                                   |                 2 |
| Spatial Contact Force (×2)                                     |                 8 |
| Frame transforms (joint → segment connections, ×many)          |                16 |
| Transform Sensors (joints, ×6)                                 |                12 |
| Bus creator extension (route new outputs to CombinedSignalBus) |                 3 |
| **Total**                                                      |    **~99 blocks** |

After the prune phase heuristically saves ~35 blocks, net delta is ~+64.
The measured savings must come from `matlab/output/logging_audit.json`
after a MATLAB run; do not treat `round(0.7 * signals_disabled)` as a
measured block-count delta.

## What's deliberately omitted

To keep the budget tight, the legs do NOT include:

- Cosmetic / visual mesh imports (e.g. shoe geometry). The simple
  cylindrical/brick solids visualise fine in Mechanics Explorer.
- Toe joint (metatarsophalangeal). Most modelling literature treats
  the foot as a single rigid body; toe flexion only matters at the
  finish.
- Knee flexion-limit blocks. Add later if instability shows up;
  Simscape's joint limit blocks add 4-6 blocks per joint.
- Per-axis muscle / tendon models. We're only modelling rigid-body
  dynamics with polynomial torque.

Each of these can be added in a follow-up PR if the optimisation
work needs them.

## Open questions

- **Hip translation.** The torso/pelvis chain currently has a
  Translation joint at the world frame. When we add legs, the global
  6-DOF freedom moves to the FEET vs. ground (via contact). We may
  need to re-anchor the model so that:

  - the existing `TranslationStartPosition{X,Y,Z}` controls the
    initial pelvis position
  - the ground reaction forces alone close the loop via the legs

  If the foot-vs-ground contact stiffness is high and the legs are
  stiff in their address-pose torque setpoints, this loop closure is
  stable. If not, we may need an explicit "weld pelvis to world for
  the first 5 ms" hack to settle. Verify with a 0.5 s simulation
  early.

- **Optimization theta growth.** Going from 189 → 231 dimensions
  makes fmincon-with-FD even slower (~85 sims per gradient step
  instead of ~190 → 231). At ~40 s per sim this is 2.5+ hours per
  gradient step. This is a **separate problem** that's already on
  the surrogate-model roadmap — train the surrogate on the new
  joint set so the optimiser uses cheap forward calls.
