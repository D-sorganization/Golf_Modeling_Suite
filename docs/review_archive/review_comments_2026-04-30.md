# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T22:54:26.999209

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3567: scripts/generate_portfolio_demo_output.py:52

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Match fixture simulation settings to documented demo run**

The new generator computes the reference CSV with `max_time=15.0` and `dt=0.01`, but the demo users are told to run `examples/basic_flight_simulation.py`, which uses `max_time=8.0` and `dt=0.05` plus a different carry-distance extraction path. Because these numerical settings and post-processing rules are not equivalent, the committed fixture can dri...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3567#discussion_r3172260566)

---

