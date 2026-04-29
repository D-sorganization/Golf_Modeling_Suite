# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T06:48:42.047744

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3440: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Preserve ndarray input compatibility in contains_point**

Switching to `math.hypot(*(point - self.center))` narrows accepted input shapes and now throws `TypeError` when `point` is a non-1D ndarray (for example `(1, 3)` row vectors commonly produced by slicing/batching). The previous `np.linalg.norm(...)` accepted these ndarray forms, so this introduces a runtime regression for existing callers that pass 2D s...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3440#discussion_r3161491112)

---

