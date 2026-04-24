# Review Comments Archive - 2026-04-24

Generated: 2026-04-24T13:05:37.624923

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3233: scripts/README.md:12

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Update root-path consumers when relocating API server script**

Moving `start_api_server.py` under `scripts/ci/` introduces a path regression because several required consumers still hardcode the repository root location (for example `Dockerfile` still runs `COPY ... start_api_server.py ./` and `.github/workflows/critical-files-guard.yml` still asserts the root file exists). In this commit state, Docker image...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3233#discussion_r3140031349)

---

### PR #3233: tests/launchers/test_help_dialogs.py:8

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Use the correct pytest-qt module name in importorskip**

This guard checks `pytest.importorskip("pytest_qt")`, but pytest-qt’s importable module is `pytestqt` (without the underscore). That means environments with pytest-qt installed can still skip this entire module unexpectedly, so these help-dialog tests stop executing and regressions can slip through.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3233#discussion_r3140031357)

---

