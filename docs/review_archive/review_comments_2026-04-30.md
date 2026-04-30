# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T02:02:22.478300

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #3521: .github/workflows/ci-standard.yml:None

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P0 Badge](https://img.shields.io/badge/P0-red?style=flat)</sub></sub>  Replace hosted runner in CI standard workflow**

This workflow now adds `audit-actions` with `runs-on: ubuntu-latest`, but `local-only-workflows` in the same file executes `scripts/check_local_only_workflows.py`, whose banned-token list explicitly rejects `ubuntu-latest`. On non-PR events that guard scans all workflows, so this introduces a deterministic self-failure path where CI Standard will fail even before ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3521#discussion_r3166227925)

---

### PR #3521: .github/workflows/ci-standard.yml:674

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Use a valid 40-character action SHA**

The new `actions/checkout` ref here is 41 hex characters, not a valid full Git commit SHA, so this step can fail to resolve the action version at runtime. This effectively breaks the new `audit-actions` job whenever CI Standard runs.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3521#discussion_r3166227927)

---

### PR #3521: scripts/pin_github_actions.py:63

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Reject non-40-char refs in action pin auditor**

The pinning audit treats 41-character refs as already pinned, which is incorrect for commit-SHA pinning and masks malformed refs. In this same commit, a 41-character checkout ref is introduced, and this condition allows the audit script to miss it instead of failing fast.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3521#discussion_r3166227932)

---

