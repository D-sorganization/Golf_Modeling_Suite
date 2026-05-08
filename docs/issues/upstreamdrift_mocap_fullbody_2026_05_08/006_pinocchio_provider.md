# starting-pose matcher: implement Pinocchio skeleton provider parity

## Context

Pinocchio is a good fit for fast forward kinematics and should be one of the
first non-Simscape providers wired into the matcher. Keep Pinocchio dependency
handling optional so the matcher can still run in environments without it.

## Target locations

- `src/tools/starting_pose_matcher/providers/pinocchio.py`
- `src/engines/physics_engines/pinocchio/python/`
- `tests/unit/tools/starting_pose_matcher/test_pinocchio_provider.py`

## Required behavior

- Load a URDF and optional package/mesh search paths.
- Accept a Pinocchio configuration vector `q`.
- Call `pin.forwardKinematics` and update frame placements when frame outputs
  are used.
- Map joint/frame IDs to the shared matcher vocabulary.
- Return metres in matcher world coordinates.
- Raise typed unavailable/configuration errors for missing Pinocchio, URDF, or
  frame mappings.

## Tests

- Registry import succeeds without Pinocchio installed.
- Mapping validation catches missing required frames.
- A fixture or mocked model returns all required joints.
- If a small URDF fixture exists, add a real FK smoke test behind an optional
  marker.

## Acceptance criteria

- Pinocchio provider can be selected and returns required vocabulary.
- Provider does not import Pinocchio at top-level registry import.
- README documents URDF path, package search path, and mapping config.

## Labels

`enhancement`, `pinocchio`, `physics-engine`, `parity`, `motion`, `TDD`
