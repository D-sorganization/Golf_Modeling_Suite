# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T03:25:48.776505

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4444: src/tools/starting_pose_matcher/providers/drake.py:112

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Detect SDF after XML declaration before selecting parser format**

Handle SDF detection more robustly here: many valid SDF strings begin with an XML declaration (e.g., `<?xml ...?>`) or comments before the `<sdf>` root, so `model_xml.strip().startswith("<sdf")` evaluates false and forces `"urdf"`. In that case Drake will try to parse SDF content as URDF and reject the model, so `model_xml` inputs copied from ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4444#discussion_r3208032637)

---

