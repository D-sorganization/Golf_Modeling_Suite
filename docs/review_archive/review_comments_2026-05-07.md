# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T22:39:42.396027

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #4412: src/tools/starting_pose_matcher/providers/pinocchio.py:45

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Preserve hip alias options in reverse vocabulary map**

Avoid generating `MATCHER_TO_PINOCCHIO` with a plain dict comprehension here, because duplicate values in `PINOCCHIO_TO_MATCHER_VOCAB` are collapsed and only the last alias survives. With both `"hip" -> "hip"` and `"pelvis" -> "hip"`, the reverse map forces `hip` to resolve to `pelvis`, so `_validate_vocabulary()` rejects models that expose `hip` but not...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4412#discussion_r3206518350)

---

### PR #4412: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/starting_pose_core.py:25

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Point legacy shim fallback to the actual repo root**

Update this fallback path depth: `parents[6]` resolves to `.../src/engines/Simscape_Multibody_Models`, not the repository root. In the documented legacy workflow (`python -m starting_pose_matcher` from `Motion Capture Plotter`), the shim then fails to import `src.tools.starting_pose_matcher.core` with `ModuleNotFoundError: No module named 'src'`, so the co...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4412#discussion_r3206518351)

---

### PR #4412: src/tools/starting_pose_matcher/__init__.py:16

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Decouple provider imports from optional GUI/data extras**

Importing this package eagerly imports `.core`, which requires optional deps like `pandas`; as a result, importing provider modules (for example `src.tools.starting_pose_matcher.providers.pinocchio`) fails before provider-specific dependency checks run unless the `gui-tools` extra is installed. This breaks headless/provider-only usage and contradicts ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4412#discussion_r3206518353)

---

