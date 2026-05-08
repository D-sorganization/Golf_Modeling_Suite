# 3D_FullBody_Model

A **derivative** of `3D_Golf_Model/` that adds legs, feet, and ground
contact, while pruning redundant signal logging to stay inside the
**Simscape Home license's 1000-block budget**.

## Design choice — why a fork instead of editing in place

The existing `3D_Golf_Model/GolfSwing3D_Kinetic.slx` is the working
model used by:

- the dataset generator
- `fit_swing_full_pipeline.m`
- the leaderboard and surrogate training pipelines
- every motion-matching test in CI

Touching it risks blast-radius across all of those.  This directory
holds a **build-from-source** copy: a small set of MATLAB scripts that,
when run, produce `GolfSwing3D_FullBody.slx` from the original model
without modifying it.

## Directory layout

```
3D_FullBody_Model/
  README.md                           ← this file
  docs/                               ← design notes
  matlab/
    src/
      model/                          ← outputs of build scripts
        GolfSwing3D_FullBody.slx     (generated; not in source control)
        PolynomialInputValues.mat    (copy from 3D_Golf_Model)
        inputs/
          3DModelInputs*.mat         (copies — joint-angle start poses)
      functions/                      (helpers specific to this model)
    scripts/
      build_3d_fullbody.m            ← MASTER BUILD SCRIPT
      prune_redundant_logging.m      (removes ~35-43 nonvirtual blocks
                                       worth of redundant signal logging)
      add_leg_chain.m                (adds two legs, two feet, ground
                                       contact)
      validate_3d_fullbody.m         (block-count + signal-count +
                                       smoke-sim checks)
      (note: directory deliberately not named "build/" because the
       repo root .gitignore filters that name everywhere)
    tests/
      test_3d_fullbody_loads.m
```

## How to build

In MATLAB R2025b on a machine with Simscape Multibody Home or Pro:

```matlab
cd .../UpstreamDrift/src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts
build_3d_fullbody
```

That single call:

1. Loads the original `3D_Golf_Model/.../GolfSwing3D_Kinetic.slx`.
2. Saves a copy as `3D_FullBody_Model/.../GolfSwing3D_FullBody.slx`.
3. Calls `prune_redundant_logging` on the copy.
4. Calls `add_leg_chain` on the copy.
5. Saves.
6. Calls `validate_3d_fullbody` (block count, signal count, brief sim).

The resulting `.slx` is committed (so a teammate without MATLAB Pro can
still simulate it) but rebuildable on demand.  A diff between two
runs of the build script is reproducible.

## Block budget

| | Estimate |
|---|---:|
| Original model nonvirtual blocks | 650-750 |
| After `prune_redundant_logging` | 615-715 (saves ~35) |
| Legs + feet + ground contact | +70-95 |
| **After `add_leg_chain`** | **685-810 / 1000** |
| Headroom remaining | 190-315 |

See [GitHub issue #4382](https://github.com/D-sorganization/UpstreamDrift/issues/4382)
for the full audit.

## What's pruned

`prune_redundant_logging.m` disables `LogSimulationData` on:

- Inertia sensors of cosmetic / non-critical solid bodies
  (~6-8 sensors).
- Per-axis duplicate logs of joint positions/velocities/accelerations
  that the consumer code can derive (`AngularKinematicsLogs/HipAngularPositionX/Y/Z`
  → kept; redundant per-frame body landmark logs in `*Cosmetic*` →
  removed).
- Club force/torque logged in BOTH local and global frames — keeps
  global only.

The ~115 surviving channels are exactly what `extractAllSignalsFromBus`,
`fit_swing_full_pipeline`, and the surrogate dataset generator need.

## What's added

`add_leg_chain.m` builds two leg subsystems mirroring the existing arm
naming convention.  Per leg:

- **Hip joint** — Gimbal Joint (3 DOF).  Fields:
  `LHipStartPositionX/Y/Z`, `LHipStartVelocityX/Y/Z`,
  `LHipPolynomial<A..G>` and the right-side equivalents.
- **Knee joint** — Revolute Joint (1 DOF).  Fields:
  `LKneeStartPosition`, `LKneeStartVelocity`, `LKneePolynomial<A..G>`.
- **Ankle joint** — Universal Joint (2 DOF).  Fields:
  `LAnkleStartPositionX/Y`, `LAnkleStartVelocityX/Y`,
  `LAnklePolynomial<A..G>`.
- **Upper leg, lower leg, foot** — Cylindrical / Brick solids with
  segment lengths from new model-workspace variables
  (`UpperLegLength`, `LowerLegLength`, `FootLength`,
  `UpperLegMass`, …).
- **Foot ↔ ground contact** — a Sphere / Plane Spatial Contact Force
  per foot against an Infinite Plane at z=0.

`getPolynomialParameterInfo()` will pick up the new joint families
automatically because it discovers them by name pattern (`<Joint><A..G>`).
That means **the existing optimiser pipeline gets ~6 new joints "for
free"** — `theta` length grows from `27 * 7 = 189` to `33 * 7 = 231`.

## Status

- [x] Directory scaffolded
- [x] Input MATs copied
- [x] Build scripts authored (this PR)
- [ ] Build scripts executed in MATLAB (requires user)
- [ ] Validation (block count + signal count + smoke sim)
- [ ] Tests (pytest + MATLAB)

## Relationship to the issue tracker

- [#4382](https://github.com/D-sorganization/UpstreamDrift/issues/4382)
  — full audit + design plan that motivated this directory.
- New issues (one per phase) will be filed when the master build
  script is run successfully and we validate against the budget.
