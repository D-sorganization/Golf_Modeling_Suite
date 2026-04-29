# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T04:48:46.804336

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3428: src/robotics/planning/collision/_primitive_shapes.py:None

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Preserve non-1D input handling in distance checks**

Switching from `np.linalg.norm(point - self.center)` to `math.hypot(*(point - self.center))` changes runtime behavior for valid NumPy inputs that are not 1-D (for example a 3x1 column vector): `np.linalg.norm` returned a scalar norm, but `math.hypot` now raises `TypeError` because unpacked elements are arrays. Since `contains_point` does not normalize or va...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3428#discussion_r3160662261)

---

## Reviewer (google-labs-jules[bot]) (1 comments)

### PR #3428: src/robotics/planning/collision/_primitive_shapes.py:None

Actionable: No
Has Suggestion: No

```
Great catch! I've wrapped the unpacked arguments in `np.ravel(...)` so `math.hypot(*np.ravel(...))` will safely and consistently flatten arbitrary shape NumPy arrays (like 3x1 column vectors) into 1D sequences before unpacking. Thanks!
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3428#discussion_r3160673734)

---

