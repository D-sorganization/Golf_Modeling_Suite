# Review Comments Archive - 2026-04-28

Generated: 2026-04-28T07:58:34.315922

## Reviewer (chatgpt-codex-connector[bot]) (4 comments)

### PR #3398: .github/workflows/Jules-Code-Quality-Fixer.yml:111

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep branch prefix consistent for PR reuse**

This branch now uses `fix/code-quality-...`, but the reuse query in the same step still filters open PR heads with `startswith("jules/code-quality-fix-")` (line 98). Because the prefixes no longer match, `EXISTING_PR` will never be found after the migration, so each run creates a fresh PR instead of updating the existing automation PR.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3398#discussion_r3154905734)

---

### PR #3398: .github/workflows/Jules-Issue-Resolver.yml:125

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Align issue-resolver branch naming with lookup filter**

The workflow now creates `fix/issue-resolver-...` branches, but it still looks up existing PRs using `startswith("jules/issue-resolver-")` (line 112). This mismatch makes the reuse path unreachable, so scheduled runs will continually open new resolver PRs instead of iterating on one branch.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3398#discussion_r3154905742)

---

### PR #3398: .github/workflows/Jules-PR-Cleanup.yml:94

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Restrict PR cleanup matching to bot-owned branches**

This selector now classifies every `fix/*` and `docs/*` branch as a Jules PR. In repositories where humans use those common prefixes, the cleanup job can incorrectly include their PRs in `/tmp/stale_prs.json` and then close them (and delete branches) when stale/failing, even though they are not automation PRs.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3398#discussion_r3154905750)

---

### PR #3398: .github/workflows/Jules-Supersede-Check.yml:91

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Limit supersede check to automation PR branches**

By broadening the filter to `^fix/|^docs/`, this workflow now treats non-Jules PRs as candidates for supersede auto-closure. On any push to `main`, a human PR on `fix/*` or `docs/*` with >=50% file overlap can be auto-closed and have its branch deleted, which is outside the intended scope of 'Jules PRs'.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3398#discussion_r3154905754)

---

