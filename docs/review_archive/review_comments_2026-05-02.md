# Review Comments Archive - 2026-05-02

Generated: 2026-05-02T07:50:27.345524

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3700: src/shared/python/humanoid_character_builder/mesh/_cg_primitive_fitting.py:75

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Cast vertices to float before einsum radius calculation**

This change can silently corrupt sphere fits when `mesh.vertices` is an integer dtype (especially `int32`): `np.einsum('ij,ij->i', vertices, vertices)` accumulates in the integer dtype, so large coordinates overflow before `np.max`, and `np.sqrt` then yields `nan` or an incorrect radius. The previous `np.linalg.norm(..., axis=1)` path computes in floa...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3700#discussion_r3176712059)

---

