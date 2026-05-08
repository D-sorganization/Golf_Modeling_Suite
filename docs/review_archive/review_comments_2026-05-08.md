# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T14:19:59.100897

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4638: tests/integration/motion_pipeline/test_loader_golden_roundtrip.py:46

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Restrict registry skip to truly missing registry module**

Catching any `ImportError` while importing `sources.registry` will skip the entire suite even when the registry exists but is broken (for example, a typo or bad transitive import inside `registry.py`). In that case CI reports skipped instead of failed, so adapter regressions are silently hidden. The skip should only trigger for the specific “module do...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4638#discussion_r3211415040)

---

### PR #4638: tests/integration/motion_pipeline/test_loader_golden_roundtrip.py:80

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Do not skip all loader ImportErrors as optional deps**

Treating every `ImportError` from `load_any(...)` as an optional dependency miss will also swallow real adapter bugs (e.g., broken internal imports) and mark them as skipped. Once adapters land, this makes the golden round-trip test unable to catch a whole class of regressions and can leave broken loaders undetected in CI.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4638#discussion_r3211415042)

---

