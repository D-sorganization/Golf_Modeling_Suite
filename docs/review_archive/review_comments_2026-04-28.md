# Review Comments Archive - 2026-04-28

Generated: 2026-04-28T01:10:44.645837

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3349: .github/workflows/Jules-Code-Quality-Fixer.yml:111

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Align branch reuse filter with new fix prefix**

In `Find or Create Fix Branch`, this workflow now creates branches as `fix/code-quality-...`, but the existing-PR lookup still filters only `jules/code-quality-fix-...` (`startswith(...)` in the same step). That makes `EXISTING_PR` miss previously opened fix branches, so each run creates a new branch/PR instead of reusing and updating the existing one, which br...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3349#discussion_r3152381135)

---

### PR #3349: .github/workflows/Jules-Issue-Resolver.yml:125

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Keep issue-resolver PR detection in sync with branch name**

This step now creates `fix/issue-resolver-...` branches, but the pre-check still searches open PRs with `startswith("jules/issue-resolver-")`. As a result, the workflow cannot find and reuse its own active PR branch and will repeatedly open new PRs on subsequent runs, defeating the "Find or Create Fix Branch" logic.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3349#discussion_r3152381137)

---

