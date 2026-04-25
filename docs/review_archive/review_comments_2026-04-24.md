# Review Comments Archive - 2026-04-24

Generated: 2026-04-24T17:05:46.049452

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #3244: scripts/README.md:16

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Update CI check invocations to new scripts/ci paths**

This change moves the CI helper scripts under `scripts/ci/`, but the CI workflow still invokes the old paths (`python3 scripts/check_file_size_budget.py`, `scripts/check_tutorial_imports.py`, and `scripts/check_pip_audit_waivers.py` in `.github/workflows/ci-standard.yml`, lines 186/192/237). At this commit those legacy files no longer exist, so the standa...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3244#discussion_r3140868295)

---

### PR #3244: scripts/README.md:12

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Fix Dockerfile COPY path for moved API server launcher**

Relocating `start_api_server.py` under `scripts/ci/` breaks container builds because `Dockerfile` still copies `start_api_server.py` from the repository root (line 101 in this commit). Since that root file was removed by this rename, `docker build` fails at the COPY step.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3244#discussion_r3140868299)

---

### PR #3244: tests/launchers/test_help_dialogs.py:8

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Gate Qt tests with the correct pytest-qt module name**

Using `pytest.importorskip("pytest_qt")` will skip this entire test module even when `pytest-qt` is installed, because the plugin’s importable module is `pytestqt` (no underscore). That turns launcher UI tests into silent skips and reduces coverage in environments that otherwise satisfy dependencies.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3244#discussion_r3140868300)

---

