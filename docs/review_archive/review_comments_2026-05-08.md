# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T14:37:12.542803

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4645: tests/unit/motion_pipeline/scaling/conftest.py:36

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Avoid global invariant monkeypatch in test conftest**

This conftest permanently replaces `src.shared.python._contracts_primitives.invariant` and `src.shared.python.contracts.invariant` at import time, and never restores them, so later tests in the same pytest session see `invariant(...)` as a no-op. That causes cross-suite contamination (for example, invariant-behavior tests outside `motion_pipeline` no long...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4645#discussion_r3211488931)

---

