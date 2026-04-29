# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T10:22:20.365365

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3469: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep point arrays 1D before calling math.hypot**

`Sphere.contains_point` no longer squeezes the input delta before unpacking into `math.hypot`, so valid NumPy row-vector inputs like shape `(1, 3)` now raise `TypeError` (`only 0-dimensional arrays can be converted to Python scalars`) instead of returning a boolean. Because this method accepts a generic `np.ndarray` and does not enforce `(3,)`, callers that pa...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3469#discussion_r3162894805)

---

### PR #3469: src/robotics/planning/collision/_primitive_shapes.py:219

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Normalize capsule distance vector before hypot unpacking**

`Capsule.contains_point` has the same regression: unpacking `point - closest` directly into `math.hypot` breaks when `point` is not strictly 1D (for example `(1, 3)` arrays), causing a runtime `TypeError`. The prior implementation handled these shapes by squeezing/normalizing first, so this change can crash collision checks for callers using batched/...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3469#discussion_r3162894813)

---

