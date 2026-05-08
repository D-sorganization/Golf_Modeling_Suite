# starting-pose matcher: implement MuJoCo skeleton provider parity

## Context

The original port issue #4367 is closed, but MuJoCo provider parity is not
implemented. Add a MuJoCo provider that maps model-native bodies/sites to the
shared matcher skeleton vocabulary.

## Target locations

- `src/tools/starting_pose_matcher/providers/mujoco.py`
- `src/engines/physics_engines/mujoco/`
- `src/shared/python/motion_matching/`
- `tests/unit/tools/starting_pose_matcher/test_mujoco_provider.py`

## Required behavior

- Load a configured MJCF/XML model path from provider config or explicit path.
- Accept a pose vector/configuration in MuJoCo `qpos` order.
- Use `mujoco.MjModel` and `mujoco.MjData`; call `mj_forward` before reading
  body/site positions.
- Map MuJoCo body/site names to:

```text
hip, spine, torso, hub, ls, rs, le, re, lw, rw, mp, ch
```

- Return positions in metres in the matcher world frame.
- Raise a typed unavailable error if MuJoCo is not installed.

## Tests

- Unit test provider import without MuJoCo installed does not break registry
  import.
- Mocked or fixture-backed provider returns required vocabulary.
- Missing body/site mapping produces a clear error listing missing joints.
- If an existing lightweight MuJoCo test fixture exists, run a real FK smoke
  test.

## Acceptance criteria

- MuJoCo appears as a selectable provider when the dependency is available.
- Provider parity tests pass for required vocabulary.
- Documentation names the body/site mapping table and coordinate-frame
  convention.

## Labels

`enhancement`, `mujoco`, `physics-engine`, `parity`, `motion`, `TDD`
