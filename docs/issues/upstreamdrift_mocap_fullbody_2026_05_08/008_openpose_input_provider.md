# starting-pose matcher: normalize OpenPose and MediaPipe as observed-input providers

## Context

OpenPose and MediaPipe are not physics engines. They provide observed human
keypoints from images/video and should feed the matcher as target observations.
This issue defines that integration without forcing them into the physics
engine provider family.

## Target locations

- `src/tools/starting_pose_matcher/providers/openpose.py`
- `src/tools/starting_pose_matcher/providers/mediapipe.py` if MediaPipe is
  supported separately
- `src/shared/python/motion_matching/`
- `tests/unit/tools/starting_pose_matcher/test_observed_input_providers.py`

## Required behavior

- Load OpenPose JSON output and normalize person keypoints into matcher target
  coordinates.
- Support MediaPipe landmarks if the repository already contains or wants that
  dependency path.
- Map observed landmarks to the shared vocabulary where possible:

```text
hip, spine, torso, hub, ls, rs, le, re, lw, rw, mp, ch
```

- Track confidence per landmark.
- Represent missing or low-confidence landmarks explicitly; do not silently
  invent points.
- Store camera/calibration metadata when available.

## Tests

- Parse a small OpenPose JSON fixture.
- Confidence thresholding preserves missing/low-confidence status.
- Mapping returns required upper-body points when present.
- Missing lower-confidence observations produce actionable UI warnings.

## Acceptance criteria

- The matcher can load observed keypoint targets through the same target/session
  schema as xlsx/C3D targets.
- OpenPose/MediaPipe code is not mixed into physics-engine providers.
- README documents the difference between physics providers and observed-input
  providers.

## Labels

`enhancement`, `pose-estimation`, `data-io`, `motion`, `TDD`
