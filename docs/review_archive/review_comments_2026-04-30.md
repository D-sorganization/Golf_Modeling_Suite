# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T01:04:39.820376

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3524: .github/workflows/ci-standard.yml:63

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P0 Badge](https://img.shields.io/badge/P0-red?style=flat)</sub></sub>  Run audit-actions on a local self-hosted runner**

Using `runs-on: ubuntu-latest` here makes `ci-standard.yml` fail its own `local-only-workflows` guard, because `scripts/check_local_only_workflows.py` explicitly bans the token `ubuntu-latest` and this workflow executes that guard on non-PR events against all workflow files. As a result, routine `push`/`schedule` runs of CI Standard will fail immediately even wh...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3524#discussion_r3166464042)

---

