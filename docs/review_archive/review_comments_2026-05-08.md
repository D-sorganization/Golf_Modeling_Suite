# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T05:25:03.693205

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4459: src/tools/starting_pose_matcher/providers/drake.py:115

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Classify model XML by root tag, not regex scan**

The new `re.search(r'<sdf[\s>]', xml_stripped[:500])` heuristic can misclassify inputs and force the wrong parser mode: a URDF containing `<sdf ...>` inside an XML comment/header will be treated as SDF, and a valid SDF whose root tag appears after a long prolog/comment (>500 chars) will be treated as URDF. In both cases `AddModelFromString(..., "sdf"|"urdf")` ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4459#discussion_r3208614767)

---

