# starting-pose matcher: implement Drake skeleton provider parity

## Context

The matcher needs Drake parity through the same provider contract used by
Simscape and MuJoCo. Drake-specific plant setup and body-frame evaluation
should stay isolated in a provider module.

## Target locations

- `src/tools/starting_pose_matcher/providers/drake.py`
- `src/engines/physics_engines/drake/`
- `tests/unit/tools/starting_pose_matcher/test_drake_provider.py`

## Required behavior

- Load a configured URDF/SDF through Drake `MultibodyPlant`.
- Finalize the plant once per provider instance.
- Accept a Drake-position vector or named pose mapping.
- Set plant positions in context and evaluate body poses in world.
- Map body/frame names to the shared matcher vocabulary.
- Return metres in the matcher world frame.
- Raise a typed unavailable error if Drake is not installed.

## Tests

- Registry import succeeds without Drake installed.
- Mocked plant/context test verifies body-name mapping and vocabulary
  validation.
- Real smoke test may be optional/skipped when Drake is unavailable.
- Coordinate-frame conversion is covered if the existing Drake model frame
  differs from Simscape.

## Acceptance criteria

- Drake provider is lazy-loadable and registry-selectable.
- Required vocabulary is returned for configured poses.
- Documentation includes the body/frame mapping table and dependency behavior.

## Labels

`enhancement`, `drake`, `physics-engine`, `parity`, `motion`, `TDD`
