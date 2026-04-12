# Review Comments Archive - 2026-04-12

Generated: 2026-04-12T13:37:21.878211

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #2634: .github/workflows/ci-standard.yml:84

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Restore dynamic runner selection after pick-runner**

This change hard-codes `runs-on: self-hosted` even though `pick-runner` still computes a fallback to `ubuntu-latest`; as a result, when no self-hosted runner is online the job will stay queued and the workflow cannot progress. The same replacement appears across many workflows in this commit, so the fallback behavior described in the dispatcher block is ef...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2634#discussion_r3069654339)

---

### PR #2634: .github/workflows/docker-security-scan.yml:24

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep docker security scan runnable without self-hosted fleet**

Switching this job from `ubuntu-latest` to `self-hosted` removes its guaranteed execution path and makes Trivy scanning dependent on private runner availability; in environments without an online self-hosted runner, the security scan will not run and SARIF uploads stop. This is a regression from the previous always-available GitHub-hosted runner ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2634#discussion_r3069654341)

---

