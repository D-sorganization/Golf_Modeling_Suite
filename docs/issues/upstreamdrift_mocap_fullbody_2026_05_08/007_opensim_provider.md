# starting-pose matcher: implement OpenSim skeleton provider parity

## Context

OpenSim is part of the repo's biomechanical model surface and should support
the same starting-pose matcher workflow. OpenSim integration is likely heavier
than MuJoCo/Pinocchio, so the provider must keep optional dependency failures
clear and isolated.

## Target locations

- `src/tools/starting_pose_matcher/providers/opensim.py`
- `src/engines/physics_engines/opensim/python/`
- `tests/unit/tools/starting_pose_matcher/test_opensim_provider.py`

## Required behavior

- Load a configured `.osim` model path.
- Initialize system/state and apply coordinate values for a named pose.
- Realize position stage before reading body positions in ground.
- Map OpenSim bodies/frames/markers to the shared matcher vocabulary.
- Return metres in matcher world coordinates.
- Raise typed unavailable/configuration errors for missing OpenSim bindings,
  model files, or mappings.

## Tests

- Registry import succeeds without OpenSim installed.
- Mocked OpenSim model/state test validates coordinate application and mapping.
- Optional real smoke test runs only when OpenSim is available.
- Missing mapping error lists exact missing vocabulary keys.

## Acceptance criteria

- OpenSim provider follows the same provider API as other engines.
- Dependency failures are actionable.
- Documentation includes `.osim` path and mapping expectations.

## Labels

`enhancement`, `opensim`, `physics-engine`, `parity`, `motion`, `TDD`
