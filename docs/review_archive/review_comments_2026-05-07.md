# Review Comments Archive - 2026-05-07

Generated: 2026-05-07T22:38:32.163793

## Reviewer (chatgpt-codex-connector[bot]) (4 comments)

### PR #4411: src/tools/starting_pose_matcher/providers/drake.py:110

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Use AddModelsFromString for Drake XML input**

The `model_xml` code path currently calls `parser.AddModelFromString(model_xml)` without a file type, but the Drake loader used elsewhere in this repo (`drake_physics_engine.load_from_string`) uses `AddModelsFromString(content, ext)` with an explicit format. As written, constructing `DrakeSkeletonProvider(model_xml=...)` will fail at runtime on supported Drake AP...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4411#discussion_r3206512552)

---

### PR #4411: src/tools/starting_pose_matcher/providers/drake.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep all Drake aliases in matcher-to-body lookup**

Reversing `DRAKE_TO_MATCHER_VOCAB` with `{v: k for ...}` drops duplicate aliases, so both `"hip"` and `"pelvis"` mapping to matcher `"hip"` collapses to only one source name (`"pelvis"`). `_validate_vocabulary()` and `get_skeleton()` then require that single surviving name, causing valid models that only expose `hip` to be rejected even though `hip` is liste...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4411#discussion_r3206512556)

---

### PR #4411: src/tools/starting_pose_matcher/providers/mujoco.py:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep all MuJoCo aliases in matcher-to-body lookup**

The MuJoCo provider has the same alias-collapse bug: inverting `MUJOCO_TO_MATCHER_VOCAB` with a dict comprehension loses one of the `hip` synonyms (`hip` vs `pelvis`) and retains only the last key. This makes `_validate_vocabulary()` reject models that define `hip` but not `pelvis`, despite the forward mapping declaring both as accepted aliases, and it can ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4411#discussion_r3206512558)

---

### PR #4411: src/tools/starting_pose_matcher/gui.py:499

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Load Simscape skeleton JSONs from export directory**

After moving the launcher entry to `src/tools/starting_pose_matcher/__main__.py`, this code now anchors skeleton lookup to `Path(__file__).parent` in the new tool directory, but `export_default_skeleton.m` still writes `simscape_skeleton_<pose>.json` to the legacy Motion Capture Plotter folder. In normal use this causes the JSONs to be missed and `load_ske...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4411#discussion_r3206512563)

---

