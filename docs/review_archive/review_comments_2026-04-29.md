# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T05:38:58.481533

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3431: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Handle non-flat point arrays in sphere containment**

Using `math.hypot(*(point - self.center))` raises `TypeError` when callers pass a 2D point shape such as `(1, 3)` (for example from `np.atleast_2d`), because unpacking supplies row arrays instead of scalars. The previous `np.linalg.norm` path accepted these inputs and returned a scalar distance, so this change introduces a runtime regression for code paths...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3431#discussion_r3161011797)

---

### PR #3431: src/robotics/planning/collision/_primitive_shapes.py:219

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Handle non-flat point arrays in capsule containment**

This `math.hypot(*(point - closest))` call has the same regression: if `point` is a row vector `(1, 3)` or other non-1D array, unpacking passes array objects to `math.hypot`, which fails with `TypeError`. The prior `np.linalg.norm` implementation handled these array shapes, so this can now break containment checks in callers that normalize inputs to 2D ar...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3431#discussion_r3161011807)

---

