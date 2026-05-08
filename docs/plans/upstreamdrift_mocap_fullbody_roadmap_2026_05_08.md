# UpstreamDrift Mocap, Starting-Pose, and Full-Body Roadmap

Last updated: 2026-05-08 UTC / 2026-05-07 Pacific

This roadmap captures the current state of the starting-pose matcher,
motion-capture alignment work, and the Simscape full-body model effort.
It is written for low-context implementation agents: each lane names the
active branch/PR, the intended repo location, the architectural contract,
and the acceptance checks that must be true before the work is considered
done.

## Current GitHub State

| Item                                             | State                                    | Meaning                                                                                                                                                                                                                   |
| ------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR #4383 `feat/starting-pose-matcher`            | Open, mergeable, unstable                | Preferred matcher relocation branch. It moves the matcher to `src/tools/starting_pose_matcher/`, adds shared-FK adoption, and updates root agent guidance. It still needs CI cleanup before merge.                        |
| PR #4379 `feat/starting-pose-matcher-relocation` | Open, unstable                           | Older overlapping relocation branch. Treat as superseded unless it contains a specific artifact missing from #4383.                                                                                                       |
| PR #4386 `feat/3d-fullbody-scaffold`             | Open, clean metadata, no checks reported | Scaffold branch for `3D_FullBody_Model`. It advances issue #4382 but does not complete the production full-body model because `add_leg_chain.m` is still a scaffold.                                                      |
| Issue #4366                                      | Closed                                   | Original Simscape input-MAT editor request. Current code does not yet provide the production MAT editing workflow, so follow-up issue `001` below reopens that product scope without changing the historical issue state. |
| Issue #4367                                      | Closed                                   | Original request to port matcher to MuJoCo, Drake, and Pinocchio. Current code only establishes a provider seam and JSON provider, so follow-up issues `003` through `008` split the real parity work by backend.         |
| Issue #4376                                      | Open                                     | Should be closed by #4383 after CI is green.                                                                                                                                                                              |
| Issue #4377                                      | Open                                     | Root `AGENTS.md` directory map. #4383 edits this file but is not currently formally linked as a closer.                                                                                                                   |
| Issue #4382                                      | Open                                     | Logging prune plus legs/feet/contact under the 1000-block Home-license budget. #4386 advances this but should not close it until scripted leg/contact construction and measured validation exist.                         |

## Product Shape

The product should be one coherent pose-matching and full-body modelling
workflow, not a set of unrelated scripts.

### Starting-Pose Matcher

Canonical location after #4383:

```text
src/tools/starting_pose_matcher/
  README.md
  __init__.py
  __main__.py
  core.py
  gui.py
  skeleton_provider.py
  providers/
    simscape.py
    mujoco.py
    drake.py
    pinocchio.py
    opensim.py
    openpose.py
```

The matcher should stay engine-agnostic at the GUI level. `gui.py` can
choose providers and render skeletons, but it should not know how MuJoCo,
Drake, Pinocchio, OpenSim, Simscape, OpenPose, or MediaPipe compute joint
positions. Provider code owns those engine details.

The shared skeleton vocabulary is intentionally compact:

```text
hip, spine, torso, hub, ls, rs, le, re, lw, rw, mp, ch
```

Providers may expose richer landmarks internally, but the matcher parity
contract compares this shared vocabulary first. Optional provider-specific
landmarks can be added later only after the shared contract is stable.

### Motion-Capture Inputs

Motion-capture target loading should go through the shared motion-matching
loading layer, especially:

```text
src/shared/python/motion_matching/load_club_target.py
```

Engine providers must not each grow their own C3D/xlsx parsing stacks.
OpenPose and MediaPipe belong in the input-observation family: they are
sources of observed human keypoints, not physics engines. Their output
should be normalized into the same target/session schema used by the
matcher and optimizer.

### Full-Body Simscape Model

PR #4386 introduces this derivative model location:

```text
src/engines/Simscape_Multibody_Models/3D_FullBody_Model/
  README.md
  .gitignore
  docs/
    LEG_CHAIN_DESIGN.md
  matlab/
    src/model/
      PolynomialInputValues.mat
      inputs/
        3DModelInputs.mat
        3DModelInputs_Impact.mat
        3DModelInputs_TopofBackswing.mat
    scripts/
      build_3d_fullbody.m
      prune_redundant_logging.m
      add_leg_chain.m
      validate_3d_fullbody.m
    tests/
      test_3d_fullbody_loads.m
```

The derivative model should be generated through MATLAB/Simulink scripts.
Do not hand-edit `.slx` internals. Do not hand-edit text `.mdl` files as a
substitute for scripted generation unless the repo deliberately converts a
model to a text format and adds a review policy for doing so. The existing
source model is `.slx`; for this repository, model edits should be
captured as MATLAB scripts plus measured validation output.

## Issue Set

The detailed GitHub issue bodies live in:

```text
docs/issues/upstreamdrift_mocap_fullbody_2026_05_08/
```

Recommended implementation order:

| Order | GitHub issue | Issue body                                 | Purpose                                                                    |
| ----- | ------------ | ------------------------------------------ | -------------------------------------------------------------------------- |
| 001   | #4387        | `001_starting_pose_mat_editor.md`          | Finish the real Simscape MAT editor product surface.                       |
| 002   | #4388        | `002_starting_pose_provider_contract.md`   | Lock the provider registry, schemas, and parity tests.                     |
| 003   | #4389        | `003_simscape_provider.md`                 | Promote Simscape JSON/FK support into a first-class provider.              |
| 004   | #4390        | `004_mujoco_provider.md`                   | Implement MuJoCo skeleton provider parity.                                 |
| 005   | #4391        | `005_drake_provider.md`                    | Implement Drake skeleton provider parity.                                  |
| 006   | #4392        | `006_pinocchio_provider.md`                | Implement Pinocchio skeleton provider parity.                              |
| 007   | #4393        | `007_opensim_provider.md`                  | Implement OpenSim skeleton provider parity.                                |
| 008   | #4394        | `008_openpose_input_provider.md`           | Normalize OpenPose/MediaPipe landmarks as observed inputs.                 |
| 009   | #4395        | `009_session_schema_and_parity_matrix.md`  | Add durable session schema and cross-provider parity tests.                |
| 010   | #4396        | `010_fullbody_scaffold_hardening.md`       | Make #4386 mergeable, isolated, and internally consistent.                 |
| 011   | #4397        | `011_logging_audit_measurement.md`         | Convert logging-prune estimates into measured audit artifacts.             |
| 012   | #4398        | `012_fullbody_leg_chain_one_side.md`       | Implement the first scripted leg chain.                                    |
| 013   | #4399        | `013_fullbody_contact_and_right_leg.md`    | Mirror the second leg and add ground contact.                              |
| 014   | #4400        | `014_fullbody_theta_contract.md`           | Extend polynomial/theta contracts from 189 to 231.                         |
| 015   | #4401        | `015_fullbody_validation_gate.md`          | Add production validation gates for block budget, signals, and smoke sim.  |
| 016   | #4402        | `016_coordination_close_superseded_prs.md` | Merge/close the current active PRs in a clean order.                       |
| 017   | #4403        | `017_wire_provider_into_gui.md`            | Make the GUI consume providers instead of hardcoded Simscape files.        |
| 018   | #4404        | `018_clubtarget_loader_adapter.md`         | Replace matcher-local Wiffle loading with the canonical `ClubTarget` path. |

## Engineering Rules for Agents

- Work in clean worktrees. The main checkout may contain dirty submodules
  unrelated to this work.
- Keep #4383 and #4386 separate unless intentionally rebasing one onto the
  other. They currently overlap in matcher files, config, and docs.
- Do not repair #4379 unless a specific missing artifact is identified.
- Add tests before broad implementation where possible. For heavy MATLAB
  work, add validation scripts and reproducible transcripts even when CI
  cannot run MATLAB.
- Preserve the existing shared infrastructure. Do not duplicate mocap
  loaders, forward-kinematics code, or engine discovery logic.
- Keep `SPEC.md` current for any source-tree, tool, public API, or model
  status change.
- Keep generated Simulink artifacts reproducible. If a generated `.slx` is
  committed, document exactly which MATLAB command regenerates it and how to
  compare the validation report.
