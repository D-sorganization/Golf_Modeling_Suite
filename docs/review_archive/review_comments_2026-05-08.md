# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T19:32:32.170594

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4789: src/shared/python/body_part_viz/shapes/primitives.py:249

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reverse cylinder side triangle winding**

The two side triangles are indexed in the opposite order of an outward-facing winding, so their computed normals point inward toward the cylinder axis. Any renderer that uses face winding for back-face culling or derives lighting normals from triangle order will draw the cylinder shell inside-out (e.g., dark or disappearing side faces depending on camera/culling mode)...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4789#discussion_r3212271465)

---

### PR #4789: src/shared/python/body_part_viz/shapes/primitives.py:382

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Flip mirrored hemisphere winding for capsule bottom**

The hemisphere face construction uses a single triangle order for both `sign=+1` and `sign=-1`; mirroring the x-coordinate for the bottom hemisphere without reversing index order flips those normals inward. In renderers that rely on winding/normal direction, the lower half of the capsule will be lit/cull opposite the upper half, producing visibly incorrec...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4789#discussion_r3212271466)

---

