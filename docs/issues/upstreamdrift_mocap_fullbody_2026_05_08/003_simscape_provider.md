# starting-pose matcher: promote Simscape JSON/FK support into a first-class provider

## Context

The current matcher reads `simscape_skeleton_<pose>.json` files and falls
back to shared forward kinematics. That should become a formal Simscape
provider so future Simscape live-export and MAT editing work has one home.

## Target locations

- `src/tools/starting_pose_matcher/providers/simscape.py`
- `src/tools/starting_pose_matcher/skeleton_provider.py`
- `src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/`
- `tests/unit/tools/starting_pose_matcher/test_simscape_provider.py`

## Required behavior

- Move JSON skeleton loading behind `SimscapeJsonProvider`.
- Preserve fallback skeleton generation from shared FK/reference golfer data.
- Validate units and coordinate frame orientation at provider boundaries.
- Keep legacy imports working through compatibility shims until dependent code
  has migrated.
- Add provider metadata that distinguishes:
  - `3D_Golf_Model`
  - future `3D_FullBody_Model`
  - JSON export mode
  - live MATLAB/Simulink export mode, if implemented later

## Tests

- Loading existing JSON skeleton file.
- Missing JSON uses FK fallback with required vocabulary.
- Malformed JSON fails with a typed provider error.
- Legacy import path still resolves during migration.

## Acceptance criteria

- `JsonSkeletonProvider` either moves into `providers/simscape.py` or becomes a
  compatibility alias.
- The UI can select the Simscape provider through the registry.
- README names the exact JSON filename convention and fallback behavior.

## Labels

`enhancement`, `matlab`, `parity`, `motion`, `TDD`, `priority:high`
