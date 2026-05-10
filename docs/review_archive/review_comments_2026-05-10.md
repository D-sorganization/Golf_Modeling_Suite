# Review Comments Archive - 2026-05-10

Generated: 2026-05-10T01:00:47.053877

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #5047: src/launchers/embedded_host.py:233

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Recompute tab lookup from widgets, not cached indices**

`QTabWidget` is made movable, but `_lookup_tab` matches close requests against the cached `record.index` values, which are only refreshed on removal. After a user drags tabs to reorder them, `tabCloseRequested(index)` can resolve to the wrong record and close the wrong tool (or fail to find one), and `open_tab(tool_id)` can focus the wrong tab for the s...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/5047#discussion_r3214412873)

---

### PR #5047: src/launchers/model_card.py:None

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Enable embedded menu modes without registry preloading**

This gate disables Tab/Dock unless `is_embeddable(model_id)` is already true, but in the current tree there are no production call sites that register tools into `EMBEDDABLE_TOOL_REGISTRY` at launcher startup, so these actions remain disabled for users even after adding the menu. As a result, the new launch-mode UI is effectively unreachable unless reg...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/5047#discussion_r3214412874)

---

### PR #5047: src/launchers/launcher_simulation.py:None

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Return fallback launch mode when tab/dock embedding fails**

`launch_model` documents that it returns the mode actually dispatched, but when `_launch_in_tab`/`_launch_in_dock` falls back to `launch_model_direct` (missing host or `open_*` failure), this method still returns the originally resolved `TAB`/`DOCK`. Callers using the return value for telemetry/state will record the wrong mode in exactly those failu...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/5047#discussion_r3214412876)

---

