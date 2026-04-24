# Review Comments Archive - 2026-04-24

Generated: 2026-04-24T16:26:57.032037

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3241: examples/basic_flight_simulation.py:71

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Interpolate ground crossing before reporting carry distance**

The carry calculation uses `landing_pts[-1]`, but `simulate_trajectory()` appends a point and only then breaks when `position[2] < 0`, so this sample is already below ground. That means the reported carry is systematically overstated by up to one integration step of horizontal travel (several meters at the current `dt=0.05` and launch speed), whic...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3241#discussion_r3140767861)

---

