# starting-pose matcher: add durable session schema and cross-provider parity matrix

## Context

The matcher already saves sessions, but provider parity needs a stable schema
that can represent targets, selected providers, transforms, pose slots, and
validation results across all models. This issue prevents each provider from
inventing incompatible state.

## Target locations

- `src/tools/starting_pose_matcher/core.py`
- `src/tools/starting_pose_matcher/gui.py`
- `src/tools/starting_pose_matcher/skeleton_provider.py`
- `tests/unit/tools/starting_pose_matcher/test_session_schema.py`
- `docs/plans/upstreamdrift_mocap_fullbody_roadmap_2026_05_08.md`

## Required behavior

Define a versioned session schema containing:

- schema version
- target source metadata: xlsx, C3D, OpenPose, MediaPipe, or trajectory CSV
- provider ID and provider metadata
- model path/config path
- selected event/phase frame
- skeleton vocabulary version
- transform: Tx, Ty, Tz, Rx, Ry, Rz, scale
- confidence/quality metrics
- optional saved Simscape MAT output path

Add a parity matrix test surface:

| Provider           | Required joints              | Units            | Coordinate frame | Optional dependency behavior  |
| ------------------ | ---------------------------- | ---------------- | ---------------- | ----------------------------- |
| Simscape           | shared vocabulary            | m                | matcher world    | JSON/FK fallback              |
| MuJoCo             | shared vocabulary            | m                | matcher world    | typed unavailable             |
| Drake              | shared vocabulary            | m                | matcher world    | typed unavailable             |
| Pinocchio          | shared vocabulary            | m                | matcher world    | typed unavailable             |
| OpenSim            | shared vocabulary            | m                | matcher world    | typed unavailable             |
| OpenPose/MediaPipe | observed subset + confidence | calibrated units | target frame     | typed parse/dependency errors |

## Tests

- Session round-trip preserves provider metadata and transform values.
- Older session files migrate or fail with a clear version error.
- Parity tests verify required vocabulary for fake providers and real providers
  when dependencies are available.
- Bad provider IDs produce a user-actionable error.

## Acceptance criteria

- Session files remain usable across provider implementations.
- Provider parity is enforced by tests, not just documentation.
- README documents the schema version and migration behavior.

## Labels

`enhancement`, `parity`, `testing`, `motion`, `TDD`, `priority:high`
