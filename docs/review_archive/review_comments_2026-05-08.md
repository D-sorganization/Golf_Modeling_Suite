# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T05:18:31.463280

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4456: src/tools/starting_pose_matcher/providers/drake.py:115

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Avoid calling unsupported Parser auto-merge API**

This introduces `parser.SetPackageMapAutoMerge(True)` on every load path, but Drake’s Python `Parser` API for the supported dependency range (`drake>=1.22.0` in `pyproject.toml`) exposes methods like `SetAutoRenaming` / `SetStrictParsing`, not `SetPackageMapAutoMerge`; in those environments this will raise `AttributeError` before any model is parsed, breaking...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4456#discussion_r3208568854)

---

### PR #4456: src/tools/starting_pose_matcher/providers/drake.py:113

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Broaden SDF detection beyond a literal space after tag**

The new SDF detection only matches `"<sdf"` at position 0 or `"<sdf "` in the first 200 characters, so valid XML such as `<?xml ...?><sdf\nversion="...">...` is misclassified as URDF when the root tag is not on one line; that causes `AddModelFromString(..., "urdf")` to fail for otherwise valid SDF inputs.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4456#discussion_r3208568859)

---

