# Review Comments Archive - 2026-04-28

Generated: 2026-04-28T05:21:28.766750

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3373: .github/workflows/Jules-Code-Quality-Fixer.yml:111

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Align PR reuse query with renamed code-quality branches**

After switching new branches to `fix/code-quality-fix-*`, the same step still searches open PRs with `startswith("jules/code-quality-fix-")`, so it will never detect an existing PR and will open a fresh one on each run. This breaks the intended reuse/update flow in the "Find or Create Fix Branch" step and can quickly create duplicate automation PRs.

...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3373#discussion_r3154041470)

---

### PR #3373: .github/workflows/Jules-Issue-Resolver.yml:125

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Align PR reuse query with renamed issue-resolver branches**

This branch is now created as `fix/issue-resolver-*`, but the existing-PR lookup in the same step still filters with `startswith("jules/issue-resolver-")`. In runs where an open resolver PR already exists, the workflow will fail to reuse it and will create another PR instead, causing avoidable PR churn.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3373#discussion_r3154041481)

---

