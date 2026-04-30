# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T20:24:53.359296

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3497: CLAUDE.md:5

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reinstate no-direct-push rule for main**

This change removes the explicit safeguard `Never push directly to main`, and the new wording (`All work on main branch. PRs target main.`) can be interpreted by automation agents as permission to commit directly to `main`, bypassing review and CI gates that only run through PR flow. Because this file is used as operational guidance, losing that constraint can cause p...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3497#discussion_r3165434526)

---

