# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T08:05:42.898316

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3446: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Flatten sphere point delta before math.hypot**

This call now throws `TypeError` when `point` is a row vector (shape `(1, 3)`), because `*(point - self.center)` unpacks to a NumPy array argument instead of scalar coordinates; that scenario is common when selecting one point from a batched `(N, 3)` array. The previous `np.linalg.norm` implementation accepted that input and returned a distance, so this is a beh...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3446#discussion_r3161764722)

---

### PR #3446: src/robotics/planning/collision/_primitive_shapes.py:219

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Flatten capsule point delta before math.hypot**

The same unpacking pattern fails for batched/row-vector inputs: if `point` is `(1, 3)`, `point - closest` is 2-D and `math.hypot(*(point - closest))` raises `TypeError` instead of returning a distance. Since the prior `np.linalg.norm` path handled these inputs, this commit introduces a new runtime failure mode in `Capsule.contains_point` for valid-looking NumPy...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3446#discussion_r3161764729)

---

