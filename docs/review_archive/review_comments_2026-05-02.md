# Review Comments Archive - 2026-05-02

Generated: 2026-05-02T04:54:53.177645

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3649: src/shared/python/humanoid_character_builder/mesh/_cg_primitive_fitting.py:76

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Prevent overflow when computing radius from integer vertices**

Using `np.einsum("ij,ij->i", vertices, vertices)` keeps integer dtypes, so meshes with large `int64` coordinates (e.g. magnitudes around 3e9) overflow during squaring before `sqrt`, producing negative values and `NaN` radii. This silently propagates into `sphere_volume`/`volume_ratio` because no exception is raised, whereas the previous `np.linal...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3649#discussion_r3176568906)

---

