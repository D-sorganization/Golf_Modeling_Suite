# starting-pose matcher: formalize provider contract, registry, and shared schemas

## Context

PR #4383 introduces `src/tools/starting_pose_matcher/skeleton_provider.py`,
but the provider interface is still minimal. Before adding separate backends,
lock the contract so MuJoCo, Drake, Pinocchio, OpenSim, Simscape, OpenPose,
and MediaPipe all integrate through the same product surface.

## Target locations

- `src/tools/starting_pose_matcher/skeleton_provider.py`
- `src/tools/starting_pose_matcher/core.py`
- `src/tools/starting_pose_matcher/providers/`
- `src/shared/python/motion_matching/`
- `tests/unit/tools/starting_pose_matcher/`
- `SPEC.md`

## Required behavior

Create a provider API that includes:

- provider metadata: `name`, `engine`, `model_path`, optional `capabilities`
- `list_poses() -> list[str]`
- `get_skeleton(pose_name: str) -> Skeleton`
- optional `get_default_pose()`
- optional `load_observed_target(...)` for observation providers only
- explicit unavailable-dependency errors for optional engines

The shared skeleton vocabulary is:

```text
hip, spine, torso, hub, ls, rs, le, re, lw, rw, mp, ch
```

Every physics-engine provider must return at least these joints for each
supported pose. Optional extra landmarks may be present, but parity tests
must compare the shared vocabulary first.

## Registry

Add a registry that can resolve providers by stable IDs:

```text
simscape-json
simscape-live
mujoco
drake
pinocchio
opensim
openpose
mediapipe
```

The registry should not import heavy optional dependencies at module import
time. Use lazy import or factory functions so `python -m
src.tools.starting_pose_matcher` still starts in core-only environments.

## Tests

- Provider protocol conformance tests with a fake provider.
- Registry test that unavailable optional engines raise typed unavailable
  errors, not raw `ImportError`.
- Vocabulary validation test for missing required joints.
- Serialization test for provider metadata in session files.

## Acceptance criteria

- New providers can be added without editing `gui.py` beyond provider selection
  UI.
- Missing optional dependencies are user-actionable.
- Provider registry is documented in README and `SPEC.md`.
- Existing JSON provider behavior still works.

## Labels

`enhancement`, `architecture`, `parity`, `motion`, `TDD`, `priority:high`
