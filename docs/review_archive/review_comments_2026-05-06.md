# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T02:23:05.585466

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4062: pyproject.toml:114

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Regenerate lockfiles after adding dev dependency**

Adding `ezc3d` to the `dev` extra without committing regenerated dependency artifacts will break CI in this repo: `ci-standard.yml` runs `make sync-deps` and then enforces `git diff --exit-code -- pyproject.toml requirements.lock requirements-dev.lock environment.yml`, while `Makefile` defines `sync-deps` to rebuild `requirements-dev.lock` from `pyproject.to...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4062#discussion_r3194322272)

---

