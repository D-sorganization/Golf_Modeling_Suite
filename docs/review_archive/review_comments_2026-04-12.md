# Review Comments Archive - 2026-04-12

Generated: 2026-04-12T13:26:21.329803

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #2629: .github/workflows/ci-standard.yml:84

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Use dispatcher output for required CI jobs**

This hardcoded `self-hosted` runner bypasses the `pick-runner` fallback logic in the same workflow (which still sets `runner=ubuntu-latest` when no `d-sorg-fleet` runner is online). As a result, when self-hosted capacity is unavailable, the required CI pipeline can stay queued indefinitely instead of falling back to GitHub-hosted runners, blocking merges and relea...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2629#discussion_r3068857083)

---

