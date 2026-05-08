# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T22:37:19.295543

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4410: src/tools/starting_pose_matcher/providers/mujoco.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Preserve hip alias when building reverse mapping**

`MATCHER_TO_MUJOCO` is derived by inverting `MUJOCO_TO_MATCHER_VOCAB`, but that source map is not one-to-one (`"hip"` and `"pelvis"` both map to matcher `"hip"`). The inversion silently keeps only the last key, so `_validate_vocabulary()` now requires a `pelvis` body and rejects models that provide `hip` (which the forward map explicitly declares as valid). ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4410#discussion_r3206503266)

---

### PR #4410: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/starting_pose_core.py:25

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Point shim repo-root fallback at actual repository root**

The deprecation shim computes `_repo_root` with `parents[6]`, but for this path that resolves to `.../src/engines/Simscape_Multibody_Models`, not the repo root. In legacy invocation contexts (for example running from the old Motion Capture Plotter directory), `importlib.import_module("src.tools.starting_pose_matcher.core")` then fails with `ModuleNotF...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4410#discussion_r3206503273)

---

