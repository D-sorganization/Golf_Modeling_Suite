# Review Comments Archive - 2026-04-25

Generated: 2026-04-25T11:07:14.299801

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3282: src/shared/python/calc_backend/tests/test_inline_calcs.py:1

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep drift baseline aligned with renamed test file**

Renaming `test_calc_backend.py` to this module without updating `TOOLS_BASELINE_HASHES` in `src/shared/python/calc_backend/tests/test_calc_backend_drift.py` leaves the drift guard pointing at a non-existent path (`.../tests/test_calc_backend.py`, line 45). In `test_calc_backend_modules_match_tools_baseline`, that entry will now hit the `if not path.exists(...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3282#discussion_r3142361415)

---

