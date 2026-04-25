# Review Comments Archive - 2026-04-25

Generated: 2026-04-25T09:21:22.850604

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3258: .github/workflows/release.yml:120

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Lowercase GHCR repository path before tagging**

`docker/build-push-action` is given tags built from `${{ github.repository }}`, which can contain uppercase letters (this repo is `D-sorganization/UpstreamDrift`). Docker image references require lowercase repository components, so a release tag push will fail in `docker-publish` with an invalid reference error instead of publishing to GHCR. Please normalize th...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3258#discussion_r3142229144)

---

