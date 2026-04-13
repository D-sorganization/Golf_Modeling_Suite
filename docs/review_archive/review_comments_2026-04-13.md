# Review Comments Archive - 2026-04-13

Generated: 2026-04-13T12:09:40.597385

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #2657: .github/workflows/ci-standard.yml:62

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep dispatcher on GitHub-hosted runner for fallback**

Changing `pick-runner` to `runs-on: d-sorg-fleet` makes the fallback logic below it unreachable: this job is supposed to run even when no fleet runner is online, check availability, and then choose `ubuntu-latest` as needed. With the dispatcher itself pinned to the fleet label, any fleet outage/maintenance window (or zero online runners) leaves the workf...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2657#discussion_r3075198157)

---

