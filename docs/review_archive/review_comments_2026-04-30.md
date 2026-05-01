# Review Comments Archive - 2026-04-30

Generated: 2026-04-30T23:49:36.985261

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3576: examples/portfolio_golf_modeling_demo.py:13

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Make demo runnable from documented invocation**

The new script documents `python examples/portfolio_golf_modeling_demo.py` as its usage, but this file imports `src.shared...` directly without adding the repository root to `sys.path`; when run exactly that way from a source checkout, Python sets `sys.path[0]` to `examples/` and the import fails with `ModuleNotFoundError: No module named 'src'`, so the newly a...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3576#discussion_r3172371642)

---

