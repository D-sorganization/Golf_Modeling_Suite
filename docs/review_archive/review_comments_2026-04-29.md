# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T23:03:52.272342

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3513: .github/workflows/ci-standard.yml:65

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P0 Badge](https://img.shields.io/badge/P0-red?style=flat)</sub></sub>  Use self-hosted runner for audit-actions job**

This workflow now declares `runs-on: ubuntu-latest`, but the same workflow’s `local-only-workflows` job invokes `scripts/check_local_only_workflows.py`, whose banned-token check rejects `ubuntu-latest`. On non-PR events (e.g., `push`, `schedule`, `workflow_dispatch`), that guard scans all workflow files, so this new line makes CI fail continuously rather than only ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3513#discussion_r3165928767)

---

### PR #3513: scripts/pin_github_actions.py:77

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Fail the audit when action SHA resolution errors**

If resolving a ref fails (auth/rate-limit/network/private repo), `get_commit_sha` returns `None` and this branch silently skips recording the unpinned action; the script can still exit success, which creates a fail-open security check. In practice, an unpinned `uses: owner/action@ref` can be missed whenever resolution errors occur, so the audit should treat ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3513#discussion_r3165928775)

---

