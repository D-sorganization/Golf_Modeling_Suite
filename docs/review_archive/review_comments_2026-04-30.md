# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T01:30:21.410013

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3523: CLAUDE.md:50

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Remove incorrect single-source coverage claim**

This line now states that `pyproject.toml` `fail_under` is the single source of truth, but CI still hard-codes `--cov-fail-under=10` in `.github/workflows/ci-standard.yml` (line 342). That means contributors reading this guidance will expect a 15% enforced floor while CI continues accepting 10–14.9% coverage, so the documented quality gate is inaccurate.

Usefu...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3523#discussion_r3166293932)

---

