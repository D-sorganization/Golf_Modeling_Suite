# starting-pose matcher: replace local Wiffle loader with canonical ClubTarget adapter

## Context

The matcher currently has its own Wiffle xlsx loading code in `core.py`.
The repo already has shared motion-matching input infrastructure:

- `src/shared/python/motion_matching/load_club_target.py`
- `src/shared/python/motion_matching/club_target.py`
- `src/shared/python/motion_matching/loaders/excel.py`
- `src/shared/python/motion_matching/loaders/c3d.py`
- `src/shared/python/motion_matching/align_to_simulation_grid.py`

The matcher should become a UI adapter over this canonical target path rather
than maintaining duplicate unit conversion and frame-loading logic.

## Target locations

- `src/tools/starting_pose_matcher/core.py`
- `src/tools/starting_pose_matcher/gui.py`
- `src/shared/python/motion_matching/load_club_target.py`
- `tests/unit/tools/starting_pose_matcher/`
- Existing shared motion-matching loader tests

## Required behavior

- Replace matcher-local xlsx parsing with a small adapter that converts
  `ClubTarget` data into the matcher's display/shaft-snap structures.
- Preserve xlsx support for `Wiffle_ProV1_club_3D_data.xlsx`.
- Add C3D support in the matcher if `load_club_target` already supports it.
- Keep frame scrubber/playback behavior unchanged.
- Keep unit conversion in the shared loader path, not duplicated in matcher
  core.
- Preserve phase/event labels needed by session save/load.

## Tests

- Existing Wiffle fixture still loads and returns the same clubhead/shaft points
  within tolerance.
- C3D fixture loads through the shared path when available.
- Matcher adapter handles missing optional target fields with typed errors.
- No duplicate Wiffle unit conversion remains in matcher-specific code except
  compatibility wrappers marked for removal.

## Acceptance criteria

- The matcher consumes canonical `ClubTarget` objects or a thin adapter derived
  from them.
- Shared target loading is the only production path for xlsx/C3D target data.
- README and `SPEC.md` document the canonical target-loader relationship.

## Labels

`enhancement`, `data-io`, `c3d`, `motion`, `DRY`, `priority:high`
