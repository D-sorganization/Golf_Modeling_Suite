# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T07:34:52.378921

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3448: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Keep distance checks compatible with row-vector points**

Replacing `np.linalg.norm(point - self.center)` with `math.hypot(*(point - self.center))` changes accepted input shapes: a point shaped `(1, 3)` now raises `TypeError` because `math.hypot` receives a 1D array argument, while the previous implementation returned a valid scalar norm. This is a behavior regression for callers that pass row slices (e.g. `p...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3448#discussion_r3161810460)

---

