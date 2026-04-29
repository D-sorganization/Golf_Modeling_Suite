# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T06:43:01.444471

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3439: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Keep distance calculation robust to non-1D ndarray inputs**

Switching to `math.hypot(*(point - self.center))` makes `Sphere.contains_point` raise `TypeError` when callers pass common NumPy point shapes like `(1, 3)` (or other non-1D array forms), because `math.hypot` only accepts scalar arguments after unpacking, while the previous `np.linalg.norm` handled these arrays. This is a behavior regression introduc...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3439#discussion_r3161446551)

---
