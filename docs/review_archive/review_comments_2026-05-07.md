# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T20:58:21.188238

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #4407: src/tools/starting_pose_matcher/gui.py:487

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Load default skeleton JSONs from the exporter directory**

The relocated GUI now resolves startup skeleton files relative to `src/tools/starting_pose_matcher`, but `export_default_skeleton.m` writes `simscape_skeleton_<pose>.json` under the legacy Motion Capture Plotter directory. In a normal launcher run this path is missing, so both initial poses silently fall back to the FK placeholder skeletons instead of...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4407#discussion_r3206160624)

---

### PR #4407: src/tools/starting_pose_matcher/providers/simscape_json.py:49

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Correct the default repo-root depth for Simscape provider**

This default path climbs one directory too far (`parents[5]`), producing `<parent>/src/engines/...` outside the repository root. As a result, `get_provider("Simscape")` cannot find exported skeleton JSONs unless callers manually pass `json_dir`, so the provider unexpectedly returns fallback skeletons in default usage.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4407#discussion_r3206160626)

---

### PR #4407: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/starting_pose_core.py:20

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Keep the deprecated shim importable from its legacy folder**

The compatibility shim now imports `src.tools.starting_pose_matcher.core` unconditionally, which fails when users run the previously documented legacy entrypoint from the Motion Capture Plotter directory (where `src` is not on `sys.path`). That turns the intended one-release compatibility shim into a `ModuleNotFoundError` for existing local workflo...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4407#discussion_r3206160633)

---

