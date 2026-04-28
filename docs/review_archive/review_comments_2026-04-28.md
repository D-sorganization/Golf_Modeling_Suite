# Review Comments Archive - 2026-04-28

Generated: 2026-04-28T08:22:39.878540

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #3404: .github/workflows/Jules-PR-Cleanup.yml:94

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Keep legacy jules/* branches in stale PR filter**

The updated matcher drops `^jules/`, so any still-open automation PRs created before this rename are no longer visible to cleanup. During rollout, those legacy PRs will never be considered for stale/failing closure, which can leave abandoned bot PRs lingering indefinitely and interfere with the intended cleanup cycle. Keep `^jules/` in this query until the re...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3404#discussion_r3155266955)

---

### PR #3404: .github/workflows/Jules-Code-Quality-Fixer.yml:98

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reuse pre-migration code-quality branch names**

This PR lookup now only matches `fix/code-quality-fix-*`, so if a `jules/code-quality-fix-*` PR is already open at deployment time, the workflow won’t find it and will create a second parallel bot PR for the same job. That duplication can produce conflicting updates and extra CI load; matching both old and new prefixes during migration avoids that regression.

...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3404#discussion_r3155266963)

---

### PR #3404: .github/workflows/Jules-Issue-Resolver.yml:112

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reuse pre-migration issue-resolver branch names**

The existing-PR query now filters only `fix/issue-resolver-*`. If an older `jules/issue-resolver-*` PR is still open when this change lands, the resolver will miss it and open a new PR/branch instead of continuing the existing one, creating duplicate automation work on the same issue stream. Include both prefixes until all legacy branches are gone.

Useful? R...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3404#discussion_r3155266970)

---

