# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T17:54:29.638645

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3556: tests/test_portfolio_demo.py:18

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Guard demo execution test on Rust-kernel availability**

This test unconditionally requires `python scripts/demo/generate_portfolio_artifact.py` to succeed, but the script calls `BallFlightSimulator.simulate_trajectory(...)` (in `scripts/demo/generate_portfolio_artifact.py`) which raises `RuntimeError` when `upstream_physics` is not installed; I verified this locally and the repo’s core lane installs `.[dev]`...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3556#discussion_r3171591205)

---

### PR #3556: docs/portfolio/golf_modeling_demo.md:23

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Update demo setup to install required Rust dependency**

The reproduction instructions say to install only `.[dev]`, then run the portfolio artifact script, but that script depends on the Rust-backed simulator path and fails without `upstream_physics`. Because `pyproject.toml` keeps Rust in a separate `rust` extra, following the documented steps currently leads to a runtime failure rather than a reproducible ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3556#discussion_r3171591211)

---

