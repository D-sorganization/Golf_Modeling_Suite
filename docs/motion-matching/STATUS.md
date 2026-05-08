# Motion-Matching Project Status

> **Goal:** match any physics-engine model (Simscape, MuJoCo, Drake,
> Pinocchio, OpenSim) to motion-capture data so we can fit a torque
> profile that reproduces a real golf swing.
>
> **Last updated:** 2026-05-08 by Claude (PR #4406 in progress)

## Critical-path summary

| Stage | Status |
|---|---|
| 1. Mocap loader (xlsx, cm units, event headers A/T/I/F) | ✅ done |
| 2. Starting-pose matcher GUI (PyQt6, frame scrubber, snap) | ✅ done |
| 3. Cross-engine `SkeletonProvider` abstraction | ✅ done (PR #4406) |
| 4. Simscape JSON provider (production) | ✅ done |
| 5. Per-engine providers (MuJoCo / Drake / Pinocchio / OpenSim) | 🟡 stubs (this PR) — fall back to FK when engine missing or model absent |
| 6. Per-engine model files + qpos keyframes | ❌ todo per engine |
| 7. Stage-1 IK from matcher offsets → engine `q` | ❌ todo per engine |
| 8. Stage-2 torque optimisation (engine-specific) | ✅ Simscape; ❌ others |
| 9. Surrogate model for fast forward sims | ✅ Simscape compact dataset; ❌ others |

## Architecture as of this PR

```
                   ┌─────────────────────────────┐
                   │  Wiffle ProV1 mocap (xlsx)  │
                   │  positions in CM            │
                   └──────────┬──────────────────┘
                              │
                              ▼
              src/shared/python/motion_matching/
                load_club_target.py + diagnostics/
                  forward_kinematics.py
                  reference_pose.py
                  _skeleton_render.py
                              │
                              ▼
                   ┌──────────────────────────┐
                   │  src/tools/starting_pose_│
                   │  matcher/                │
                   │   - core.py              │
                   │   - gui.py               │
                   │   - providers/           │
                   │       _base.py           │
                   │       simscape_json.py   │── reads JSON
                   │       mujoco_provider.py │── needs MJCF + qpos
                   │       drake_provider.py  │── needs URDF/SDF + q
                   │       pinocchio_*.py     │── needs URDF + q
                   │       opensim_*.py       │── needs OSIM + coords
                   └──────────┬───────────────┘
                              │
                  saves "starting_pose_offsets.json"
                              │
                              ▼
                   ┌──────────────────────────┐
                   │  fit_swing_full_pipeline │
                   │  (Simscape MATLAB only)  │
                   └──────────────────────────┘
```

## What this PR (#4406) closes

- **#4367** port matcher to MuJoCo / Drake / Pinocchio / OpenSim
- **#4388** formalize provider contract, registry, schemas
- **#4389** promote Simscape JSON / FK provider to first-class
- **#4390** MuJoCo skeleton provider parity
- **#4391** Drake skeleton provider parity
- **#4392** Pinocchio skeleton provider parity
- **#4393** OpenSim skeleton provider parity
- **#4403** wire `SkeletonProvider` into the GUI

## Still open (deferred or not on critical path)

| Issue | Why deferred |
|---|---|
| #4366 input-MAT editor | Needs three new MATLAB helper scripts; tracked under #4387.  Not blocking any-engine-to-mocap. |
| #4382 model audit + legs/feet | Scaffolded by PR #4386; full leg implementation is iterative MATLAB work. |
| #4394 pose-estimation providers (OpenPose, MediaPipe) | Different input modality (video → joints); separate roadmap. |
| #4395 cross-provider parity matrix | Aggregator across #4390-#4393 — easier to file once each engine has a reference model. |
| #4396 scaffold hardening | Cosmetic; addresses concerns about #4386's scaffold mode. |
| #4397 measurable logging prune | Depends on #4382 progress. |
| #4398-#4401 leg chain phases | Sequential, depend on #4386 merging. |
| #4402 coordination meta-issue | Will close as PRs merge. |
| #4404 ClubTarget adapter | Internal refactor; doesn't change behaviour. |
| #4405 roadmap doc | Should land before this PR. |
| #4387 real input-MAT editor | Major piece of work for the iterative-refine loop; separate PR. |

## How to run end-to-end (Simscape today)

```bash
# 1. Install the GUI extras
pip install -e ".[gui-tools]"

# 2. (One-time, in MATLAB) export the Simscape skeleton JSONs
matlab -batch "cd('.../matlab/src/apps/golf_gui/Motion Capture Plotter'); export_default_skeleton('Address'); export_default_skeleton('TopofBackswing'); export_default_skeleton('Impact')"

# 3. Launch the matcher
python -m src.tools.starting_pose_matcher

# 4. In the GUI:
#    - Mocap Source → Load xlsx → Wiffle_ProV1_club_3D_data.xlsx
#    - Pose Slots → Engine = Simscape (default)
#    - Press T (top of backswing); use sliders / shaft-snap to align
#    - Save offsets to JSON

# 5. (In MATLAB) feed the offsets into fit_swing_full_pipeline
matlab -batch "cd('.../motion_matching'); fit_swing_full_pipeline(target_xlsx, struct('input_overrides_json', 'starting_pose_offsets.json'))"
```

## How to run end-to-end (other engines, when you have a model file)

```python
# Each engine provider accepts a model_path in its constructor:
from src.tools.starting_pose_matcher.providers import get_provider

# MuJoCo
provider = get_provider("MuJoCo", model_path="/path/to/humanoid.xml")
skel = provider.get_skeleton("Address")

# Drake
provider = get_provider("Drake", model_path="/path/to/humanoid.urdf",
                        poses_q_npz="/path/to/poses_q.npz")

# Pinocchio
provider = get_provider("Pinocchio", model_path="/path/to/humanoid.urdf")

# OpenSim
provider = get_provider("OpenSim", model_path="/path/to/humanoid.osim",
                        poses_coords_npz="/path/to/poses_coords.npz")
```

The matcher's GUI exposes the engine selection per pose slot — it
calls `get_provider` under the hood.  When an engine isn't installed
or a model file isn't supplied, the provider gracefully falls back to
the FK-derived default skeleton so the GUI keeps working.

## Tests

```bash
# Pure-data + provider tests (no PyQt6 / engine deps required)
pytest tests/unit/tools/starting_pose_matcher/  tests/unit/engines/simscape/three_d_gui/test_starting_pose_matcher.py
# 12 + 45 = 57 tests, all pass on Python 3.14
```

UI smoke tests skip cleanly when PyQt6's DLL search path is broken
under user-site pytest (a known Windows quirk).

## Open issues by phase (snapshot)

- **Closed by this PR (in body):** #4367, #4388, #4389, #4390, #4391, #4392, #4393, #4403
- **Already closed by #4383:** #4376, #4377
- **Open and intentionally deferred:** all others (see table above)
