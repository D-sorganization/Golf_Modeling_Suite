# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T07:39:00.338475

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3449: src/robotics/planning/collision/_primitive_shapes.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Preserve support for column/row vector point inputs**

Using `math.hypot(*(point - self.center))` assumes `point - self.center` is a 1D length-3 vector; if callers pass a common 3D column/row representation like shape `(3,1)` or `(1,3)`, this now raises `TypeError` instead of returning a distance as before with `np.linalg.norm`. That is a behavior regression for valid 3D coordinate data in robotics code paths...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3449#discussion_r3161838413)

---

