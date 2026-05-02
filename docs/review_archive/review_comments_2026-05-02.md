# Review Comments Archive - 2026-05-02

Generated: 2026-05-02T05:11:08.444361

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3650: src/shared/python/humanoid_character_builder/mesh/_cg_primitive_fitting.py:75

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Cast vertices to float before einsum radius computation**

Using `np.einsum('ij,ij->i', vertices, vertices)` on integer vertex arrays can overflow during the square-and-sum step, which yields incorrect radii (including `nan`) before `np.sqrt` runs. This is a regression from `np.linalg.norm(..., axis=1)`, which handled integer inputs safely via floating-point norm computation. Because `_load_mesh` passes throu...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3650#discussion_r3176585992)

---

