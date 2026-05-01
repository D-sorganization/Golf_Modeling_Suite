# Review Comments Archive - 2026-05-01

Generated: 2026-05-01T02:39:05.550799

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3617: tests/examples/test_examples_produce_output.py:46

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Build PYTHONPATH with os.pathsep**

The new `PYTHONPATH` string is joined with a hard-coded `:` delimiter, which only works on POSIX. On Windows (where `os.pathsep` is `;`), this becomes one invalid path entry (e.g., `C:\repo:C:\repo\src:...`), so `test_example_produces_output` can fail to import `src.*` modules for examples that do not self-modify `sys.path`. Please construct this value with `os.pathsep` (or...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3617#discussion_r3172760701)

---

### PR #3617: docs/portfolio/golf_modeling_demo_output.csv:9

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Keep portfolio reference values consistent with docs**

These updated fixture numbers no longer match the published reference table in `docs/portfolio/golf_modeling_demo.md` (lines 89-90 still list `187.2 m / 204.7 yd` and `42.6 m`). That breaks the demo’s reproducibility contract: a reviewer following the document will see different “expected” outputs than the committed artifact. Please update the doc table ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3617#discussion_r3172760709)

---

