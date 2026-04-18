# Review Comments Archive - 2026-04-17

Generated: 2026-04-17T21:47:42.867806

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #2759: .pre-commit-config.yaml:44

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Use an interpreter guaranteed to exist for the hook**

Switching this `language: system` hook to `python` can break contributors on environments that only expose `python3` (common on Linux images without a `python` shim). Because this hook is `always_run: true`, `git commit` will fail immediately with an executable-not-found error in those setups, so the change trades one platform-specific failure for another...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2759#discussion_r3104496228)

---

