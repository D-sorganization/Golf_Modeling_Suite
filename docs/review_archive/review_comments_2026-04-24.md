# Review Comments Archive - 2026-04-24

Generated: 2026-04-24T12:00:36.991551

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3226: scripts/verify_installation.py:254

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Point uvicorn health check at a real ASGI object**

`check_api_server()` launches uvicorn with `src.api.server:create_app`, but `src/api/server.py` defines a module-level `app` and does not export `create_app`. In this state the subprocess exits immediately, so the `/health` probe can never succeed and the API verification path reports a false failure even on valid installs (the same invalid target is also sh...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3226#discussion_r3139746655)

---

### PR #3226: tests/launchers/test_help_dialogs.py:8

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Use the correct pytest-qt module name for importorskip**

This guard checks `pytest_qt`, which causes this entire test module to be skipped in environments where pytest-qt is installed as `pytestqt` (the package name this repo already maps to in `engine_availability`). That silently removes coverage for `help_dialogs` and can let regressions ship because the tests are never executed.

Useful? React with 👍 / 👎...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3226#discussion_r3139746661)

---

