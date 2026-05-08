# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T22:42:45.600969

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #4413: src/tools/starting_pose_matcher/providers/drake.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Preserve aliases when reversing the joint-name mapping**

This reverse dict comprehension drops synonyms because multiple engine names map to the same matcher key (e.g., both `hip` and `pelvis` map to `hip`, but only the last survives). As a result, `_validate_vocabulary()` and `get_skeleton()` require only `pelvis` and will incorrectly reject models that use `hip` (or miss valid joints). This affects real mo...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4413#discussion_r3206528602)

---

### PR #4413: src/tools/starting_pose_matcher/providers/drake.py:110

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Provide file type when parsing Drake XML text**

`Parser.AddModelFromString` is called with only the XML payload, but Drake string parsing requires a format hint (`urdf`/`sdf`). In the `model_xml` path this causes provider construction to fail at runtime, so XML-based usage (including the new minimal-URDF flow) cannot work when Drake is installed.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4413#discussion_r3206528605)

---

### PR #4413: src/tools/starting_pose_matcher/providers/mujoco.py:163

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Recompute MuJoCo forward kinematics before skeleton reads**

Kinematics are only advanced when `qpos` is provided, so `get_skeleton()` with `qpos=None` reads `xipos` without a fresh `mj_forward`. On first call this returns zero/uninitialized positions, and on later calls it can return stale positions from a previous state update. This makes default skeleton extraction incorrect unless callers always pass `qpo...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4413#discussion_r3206528606)

---

