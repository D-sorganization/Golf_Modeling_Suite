# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T19:30:08.409991

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4785: src/shared/python/body_part_viz/shapes/mesh.py:263

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Apply scene transforms before concatenating GLB geometries**

When `trimesh.load(..., force="mesh")` yields a scene-like object, this code concatenates `loaded.geometry.values()` directly, which drops per-node transforms and instancing from the scene graph. For `.glb` files that position meshes via node transforms (a common case), the resulting `MeshShape` will have incorrect vertex positions/extents, causing...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4785#discussion_r3212263391)

---

### PR #4785: src/shared/python/body_part_viz/shapes/mesh.py:200

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reject non-integer face arrays instead of truncating**

`from_arrays` currently coerces non-integer `faces` to `int64`, so fractional inputs like `[[0.9, 1.1, 2.0]]` are silently truncated to `[[0, 1, 2]]` rather than being rejected. This violates the documented contract that face indices are integer triangles and can silently corrupt topology when upstream data is malformed. The constructor should raise on n...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4785#discussion_r3212263393)

---

