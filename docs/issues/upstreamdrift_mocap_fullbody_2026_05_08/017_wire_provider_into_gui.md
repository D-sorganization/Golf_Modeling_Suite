# starting-pose matcher: wire SkeletonProvider into the GUI

## Context

PR #4383 introduces `SkeletonProvider`, but the GUI still directly calls
Simscape-specific skeleton loading paths such as `simscape_skeleton_<pose>.json`.
Provider parity cannot be real until the GUI talks to a provider abstraction.

## Target locations

- `src/tools/starting_pose_matcher/gui.py`
- `src/tools/starting_pose_matcher/skeleton_provider.py`
- `src/tools/starting_pose_matcher/providers/`
- `tests/unit/tools/starting_pose_matcher/`

## Required behavior

- Add provider selection/configuration to the matcher state.
- Replace direct `load_skeleton(here / "simscape_skeleton_<pose>.json", ...)`
  calls in the GUI with provider calls.
- Store provider ID and provider config in session save/load.
- Surface typed provider errors in the UI without crashing.
- Keep existing Simscape JSON behavior unchanged through the default provider.
- Do not import heavy optional engines from `gui.py`.

## Tests

- Fake provider GUI smoke/unit test showing the GUI can load skeletons without
  Simscape JSON paths.
- Session round-trip preserves provider ID/config.
- Provider error is displayed or returned as a user-readable message.
- Existing Simscape JSON/fallback tests still pass.

## Acceptance criteria

- `gui.py` no longer hardcodes Simscape skeleton files except in default
  provider configuration.
- Adding MuJoCo/Drake/Pinocchio/OpenSim providers does not require modifying
  pose rendering logic.
- README documents how provider selection works.

## Labels

`enhancement`, `gui`, `architecture`, `parity`, `priority:high`
