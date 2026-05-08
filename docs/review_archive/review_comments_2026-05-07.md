# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T20:10:01.858298

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4386: src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/build_3d_fullbody.m:139

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Derive fullbody_root from the correct directory depth**

The default path logic climbs one level too far: from `.../3D_FullBody_Model/matlab/scripts`, `fileparts(fileparts(fileparts(here)))` resolves to `.../Simscape_Multibody_Models`, so the default `target_slx` is written under `.../Simscape_Multibody_Models/matlab/src/model/...` instead of `.../3D_FullBody_Model/matlab/src/model/...`. With default options ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4386#discussion_r3206034942)

---

### PR #4386: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/starting_pose_core.py:20

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep the legacy core shim importable from its old folder**

This shim now hard-imports `src.tools.starting_pose_matcher.core`, which requires the repository root on `sys.path`. The legacy invocation pattern from this directory (`python -m starting_pose_matcher`) does not provide that path, so importing `starting_pose_core` raises `ModuleNotFoundError: No module named 'src'`. That breaks the stated backward-co...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4386#discussion_r3206034947)

---

