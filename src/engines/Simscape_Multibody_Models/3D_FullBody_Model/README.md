# 3D_FullBody_Model

A **derivative scaffold** of `3D_Golf_Model/` for adding legs, feet,
and ground contact in follow-up work, while pruning redundant signal
logging to stay inside the **Simscape Home license's 1000-block
budget**.

## Design choice — why a fork instead of editing in place

The existing `3D_Golf_Model/GolfSwing3D_Kinetic.slx` is the working
model used by:

- the dataset generator
- `fit_swing_full_pipeline.m`
- the leaderboard and surrogate training pipelines
- every motion-matching test in CI

Touching it risks blast-radius across all of those. This directory
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
      extend_polynomial_theta_contract.m
                                      (idempotently appends full-body leg
                                       polynomial coefficient families)
      prune_redundant_logging.m      (removes ~35-43 nonvirtual blocks
                                       worth of redundant signal logging)
      add_leg_chain.m                (scripted left-leg chain slice
                                       with idempotent rebuild reporting)
      validate_3d_fullbody.m         (block-count + signal-count +
                                       smoke-sim checks)
      (note: directory deliberately not named "build/" because the
       repo root .gitignore filters that name everywhere)
    output/                           generated JSON reports
      build_report.json               build-phase metadata
      logging_audit.json              measured + heuristic prune audit
      validation_report.json          validation summary
    tests/
      test_3d_fullbody_loads.m
      test_3d_fullbody_polynomial_contract.m
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
7. Writes generated JSON reports under `matlab/output/`.

Generated artifact policy: `GolfSwing3D_FullBody.slx` is generated-only
and ignored by this directory's `.gitignore`. Review and commit the
source scripts, docs, and schema contract; rebuild the binary on a
MATLAB/Simscape machine when it is needed. If the team later decides to
vendor a validated `.slx`, that should be a separate PR that also updates
this README and `.gitignore` together.

The default report paths are:

- `matlab/output/build_report.json`
- `matlab/output/logging_audit.json`
- `matlab/output/validation_report.json`

The build and validation reports record source/target paths, phase
metadata, block counts, signal counts, smoke-sim status, and the
generated-only artifact policy. The logging audit is machine-readable
and separates measured before/after counts from heuristic savings.

## Polynomial theta contract

The checked-in full-body `PolynomialInputValues.mat` is extended from
the legacy 3D golf file by
`matlab/scripts/extend_polynomial_theta_contract.m`. The extension adds
zero-valued coefficient variables for both legs and preserves existing
values on rerun unless `overwrite=true` is passed.

Measured with MATLAB `whos('-file', ...)` and the same
`getPolynomialParameterInfo()` name-pattern discovery used by the
dataset generator:

| Model family   | Discovered families | Coefficients per family | Theta size |
| -------------- | ------------------: | ----------------------: | ---------: |
| Legacy 3D golf |                  27 |                       7 |        189 |
| 3D full-body   |                  39 |                       7 |        273 |

The full-body result is **39**, not 33, because the discovery contract
counts actuated axes as coefficient families. Hip gimbals contribute
`X/Y/Z`, ankles contribute `X/Y`, and knees contribute one family. Across
left and right legs that is 12 new axis families and 84 new coefficients.
Optimizers must not assume a 231-element vector for this model family.

## Block budget

|                                  |                                        Estimate |
| -------------------------------- | ----------------------------------------------: |
| Original model nonvirtual blocks |                                         650-750 |
| After `prune_redundant_logging`  | 615-715 (heuristic savings only until measured) |
| Legs + feet + ground contact     |                                          +70-95 |
| **After `add_leg_chain`**        |                              **685-810 / 1000** |
| Headroom remaining               |                                         190-315 |

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

The ~115 surviving channels are a target, not a measured result until
`matlab/output/logging_audit.json` is produced from a real MATLAB run.
The audit report must list the exact disabled block/outport paths and
the required downstream signal families preserved for
`extractAllSignalsFromBus`, `fit_swing_full_pipeline`, the surrogate
dataset generator, optimizer inputs, matcher inputs, and force-analysis
outputs.

## What's added

`add_leg_chain.m` currently implements the first left-leg slice. It
deletes and rebuilds the generated `Left Leg Kinetically Driven`
subsystem on every run, creates the stable hip/knee/ankle/foot anchor
blocks, and reports any MATLAB/Simscape-release-specific block, mask, or
line operation that cannot be completed in the returned
`operation_log`. The right-leg mirror and full foot-vs-ground contact
wiring remain follow-up work.
Per leg, the planned implementation is:

- **Hip joint** — Gimbal Joint (3 DOF). Fields:
  `LHipStartPositionX/Y/Z`, `LHipStartVelocityX/Y/Z`,
  `LHipPolynomial<A..G>` and the right-side equivalents.
- **Knee joint** — Revolute Joint (1 DOF). Fields:
  `LKneeStartPosition`, `LKneeStartVelocity`, `LKneePolynomial<A..G>`.
- **Ankle joint** — Universal Joint (2 DOF). Fields:
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
That means the full-body optimiser contract grows by 12 axis families:
`theta` length grows from `27 * 7 = 189` to `39 * 7 = 273`.

## Status

- [x] Directory scaffolded
- [x] Input MATs copied
- [x] Build scripts authored
- [x] One scripted left-leg chain slice
- [x] Full-body leg polynomial/theta contract extended and measured
- [ ] Build scripts executed in MATLAB (requires user)
- [ ] Validation (block count + signal count + smoke sim)
- [ ] Tests (pytest + MATLAB)

## Relationship to the issue tracker

- [#4382](https://github.com/D-sorganization/UpstreamDrift/issues/4382)
  — full audit + design plan that motivated this directory. This
  scaffold advances that issue but does not close it; full leg/contact
  validation remains follow-up work.
- New issues (one per phase) will be filed when the master build
  script is run successfully and we validate against the budget.
