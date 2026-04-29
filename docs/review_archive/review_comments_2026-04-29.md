# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T04:18:36.168363

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3427: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Preserve ndarray input compatibility in distance checks**

Replacing `np.linalg.norm` with `math.hypot(*(point - self.center))` makes `contains_point` raise `TypeError` when `point` is a 2D row vector (for example shape `(1, 3)`, which commonly comes from slicing like `points[i:i+1]`). `np.linalg.norm` previously handled these array-like inputs, so this change introduces a runtime regression for callers that ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3427#discussion_r3160532396)

---

