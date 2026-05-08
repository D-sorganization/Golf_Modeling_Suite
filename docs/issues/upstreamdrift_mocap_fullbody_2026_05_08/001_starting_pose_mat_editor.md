# starting-pose matcher: implement the real Simscape input-MAT editor workflow

## Context

The original issue #4366 is closed, but the production product scope is not
finished. The matcher can compute and save a rigid transform, but users still
need a safe workflow for editing Simscape `3DModelInputs*.mat` start-position
values, previewing the resulting pose, and saving a new MAT file without
mutating canonical inputs.

This is Simscape-specific and should sit behind the starting-pose matcher UI
and provider contract rather than becoming generic engine code.

## Target locations

- `src/tools/starting_pose_matcher/core.py`
- `src/tools/starting_pose_matcher/gui.py`
- `src/tools/starting_pose_matcher/providers/simscape.py`
- `src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/model/inputs/`
- `tests/unit/engines/simscape/three_d_gui/test_starting_pose_matcher.py`
- New focused tests under `tests/unit/tools/starting_pose_matcher/` if the
  branch has adopted that package layout.

## Required behavior

1. Load an existing Simscape input MAT file selected by the user.
2. Discover editable start-position/start-velocity fields using the same
   naming rules as the Simscape model:
   - `TranslationStartPosition{X,Y,Z}`
   - existing upper-body joint start positions
   - future full-body fields such as `LHipStartPositionX`,
     `LKneeStartPosition`, `LAnkleStartPositionX`
3. Display editable values in degrees/metres with units visible in the UI.
4. Apply the matcher transform as an overlay without immediately overwriting
   source MAT values.
5. Provide a constraint-resolved preview:
   - invalid fields are rejected with a clear validation error
   - missing optional future full-body fields are allowed only when the loaded
     model is not the full-body model
   - required current-model fields must not silently default to zero
6. Save to a new file by default, using an explicit suffix such as
   `_starting_pose_<timestamp>.mat`.
7. Never mutate canonical repo inputs unless the user explicitly chooses an
   overwrite action in the UI.

## Design constraints

- Python should use `scipy.io.loadmat` / `savemat` or an existing repository
  helper, not ad hoc binary parsing.
- The MAT editor should be provider-scoped. MuJoCo, Drake, Pinocchio, OpenSim,
  OpenPose, and MediaPipe should not see Simscape MAT fields.
- Keep UI code thin. Put MAT validation, field discovery, and save behavior in
  pure functions that can be tested without PyQt.
- Preserve session save/load. A session should record which MAT file was loaded
  and which output MAT file was written, but it should not embed large MAT
  payloads.

## Tests

- Unit test field discovery on a representative dictionary that includes
  translation, gimbal, revolute, and universal-joint fields.
- Unit test that unknown required fields produce an explicit validation error.
- Unit test that saving creates a new file path and does not mutate the input
  dictionary in place.
- Unit test that full-body-only fields are accepted when present and not
  required for legacy `3D_Golf_Model` inputs.
- GUI smoke test should skip cleanly when PyQt is unavailable.

## Acceptance criteria

- The matcher UI can load a Simscape MAT input, show editable start fields,
  preview a transform-adjusted pose, and save a new MAT file.
- Core MAT edit functions are covered without requiring MATLAB.
- The Simscape provider owns this behavior; no other provider imports Simscape
  MAT-specific code.
- `SPEC.md` and the starting-pose matcher README describe the workflow.

## Labels

`enhancement`, `matlab`, `gui`, `motion`, `TDD`, `priority:high`
