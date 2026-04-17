# Review Comments Archive - 2026-04-16

Generated: 2026-04-16T21:55:49.572466

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #2722: src/robotics/sensing/imu_sensor.py:319

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Return orientation on initial IMU read**

With `include_orientation=True`, the first `read()` call now returns `orientation=None` because the assignment is gated on `_last_timestamp` being set. That breaks callers that rely on receiving a quaternion whenever orientation output is requested (the sensor already has a valid initialized orientation), and this regression appears only on the initial sample. Keep in...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2722#discussion_r3097868179)

---

### PR #2722: src/robotics/sensing/noise_models.py:495

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Decouple bias clipping from white-noise level**

The factory now ties `BrownianNoise.max_bias` to `representative_std`, so when callers intentionally configure zero white noise (`noise_std=0` or `noise_density=0`) with nonzero `bias_drift_rate`, `max_bias` becomes `0` and the random walk is fully clipped out. This silently disables bias drift and makes bias-only simulations impossible even though `bias_drift_...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2722#discussion_r3097868183)

---

### PR #2722: src/robotics/sensing/noise_models.py:243

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Return vector initial_bias from current_bias**

The `BrownianNoise` API now accepts array-valued `initial_bias`, but `current_bias` forces a `(1,)` shape before first `apply()` (and after `reset()`), which raises `ValueError` for vector initial biases. This makes the new vector-bias mode unusable for state inspection exactly when users typically query it.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2722#discussion_r3097868185)

---

