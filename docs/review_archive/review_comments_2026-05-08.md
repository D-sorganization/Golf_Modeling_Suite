# Review Comments Archive - 2026-05-08

Generated: 2026-05-08T10:09:19.309955

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4495: tests/unit/ui/test_preferences_dialog.py:9

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Handle PyQt DLL-load failures as test skips**

Replace module-level `pytest.importorskip("PyQt6.QtWidgets")` with an explicit import guard that also catches `OSError`; `importorskip` only skips `ImportError`, so environments where PyQt6 is installed but fails to load native DLLs (a known Windows/user-site case in this repo) will raise at collection time and fail the suite instead of skipping this optional GUI...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4495#discussion_r3210175668)

---

