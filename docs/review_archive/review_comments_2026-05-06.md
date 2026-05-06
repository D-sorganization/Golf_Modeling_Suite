# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T15:02:12.784315

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4089: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/motion_matching/shared/solve_starting_pose.m:120

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Map A_sample into aligned target index before lookup**

`target.events.A_sample` is a raw sheet sample number (e.g. 240 in TW_ProV1), but this code uses it directly as an index into the already aligned/resampled `target.grip` array. On real aligned targets (typically ~301 rows around impact), that selects a near-impact row instead of the address pose, so Stage-1 optimizes to the wrong frame and can return inc...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4089#discussion_r3197766766)

---

