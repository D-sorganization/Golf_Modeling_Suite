# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T19:55:33.538088

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4383: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/starting_pose_core.py:20

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Add repo-root fallback in legacy starting_pose_core shim**

This shim now unconditionally imports `src.tools.starting_pose_matcher.core`, but legacy usage runs from `.../Motion Capture Plotter` (e.g. `python -m starting_pose_matcher`) where the repo root is not on `sys.path`, so import fails with `ModuleNotFoundError: No module named 'src'`. That breaks the promised one-release compatibility for existing call...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4383#discussion_r3205997871)

---

### PR #4383: src/tools/starting_pose_matcher/gui.py:488

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Resolve default skeleton paths after matcher relocation**

The relocated GUI still loads pose JSONs from `Path(__file__).parent`, which is now `src/tools/starting_pose_matcher/`; however `export_default_skeleton.m` writes `simscape_skeleton_*.json` to the legacy Motion Capture Plotter folder, so the new tile misses those generated files and silently falls back to approximate skeletons. In practice this can sk...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4383#discussion_r3205997874)

---

