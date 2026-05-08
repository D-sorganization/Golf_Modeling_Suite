# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T03:38:45.815433

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4446: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/starting_pose_core.py:27

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Point shim repo_root at the actual repository root**

Using `parents[10]` resolves to the directory above the repo root for this file path (e.g. `/workspace` instead of `/workspace/UpstreamDrift`), so the fallback inserts a path that still does not contain the top-level `src` package. In the legacy scenario this shim targets (repo root not already on `sys.path`), `importlib.import_module("src.tools.starting_p...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4446#discussion_r3208099552)

---

### PR #4446: src/tools/starting_pose_matcher/providers/drake.py:112

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Detect SDF content robustly before selecting parser type**

The format check only accepts strings that begin exactly with `<sdf` after trimming whitespace; valid SDF documents that start with an XML declaration (for example `<?xml ...?><sdf ...>`) are misclassified as URDF. In that case `AddModelFromString(..., "urdf")` attempts to parse SDF as URDF and model loading fails for otherwise valid `model_xml` inpu...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4446#discussion_r3208099557)

---

