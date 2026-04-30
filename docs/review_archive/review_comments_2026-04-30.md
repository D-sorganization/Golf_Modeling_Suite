# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T10:41:35.501383

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3535: .github/workflows/Bot-CI-Trigger.yml:80

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Pin checkout to a v6 commit instead of v4.1.1**

This SHA (`b4ffde65f46336ab88eb53be808477a3936bae11`) is the `actions/checkout` `v4.1.1` tag, so this change silently downgrades every workflow from `@v6` to an Oct 2023 implementation. That is not behavior-preserving pinning: it drops all v5/v6 fixes and can break workflows that depend on newer checkout behavior (the repo currently references `@v6` across many...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3535#discussion_r3169777527)

---

### PR #3535: .github/workflows/Code-Metrics.yml:47

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Pin setup-python to a v6 commit instead of v5.1.0**

This SHA (`82c7e631bb3cdc910f68e0081d67478d79c6982d`) maps to `actions/setup-python` `v5.1.0`, so replacing `@v6` with it downgrades the action rather than just making it immutable. That rollback removes v6-era updates (including the node24/runtime line and later fixes), and can cause CI drift versus the previously requested `v6` behavior. Pin to a commit t...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3535#discussion_r3169777533)

---

