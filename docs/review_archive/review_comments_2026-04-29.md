# Review Comments Archive - 2026-04-29

Generated: 2026-04-29T04:59:38.031053

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3424: src/shared/python/ml/dataset_generator.py:None

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Don't swallow engine step AttributeErrors**

Catching `AttributeError` around `self.engine.step(...)` will also swallow `AttributeError`s raised *inside* a buggy engine implementation, so dataset generation continues and records frames after a failed step. In that case the run is silently corrupted (stale/invalid state data) instead of failing fast, and the warning message implies a fallback path that never a...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3424#discussion_r3159965152)

---

### PR #3424: src/shared/python/signal_toolkit/signal_processing.py:203

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Handle unreachable DTW paths instead of returning sentinel distance**

When the Sakoe-Chiba window makes alignment impossible (e.g., `compute_dtw_path` with unequal lengths and `window=0`), `dtw_matrix[n, m]` remains the sentinel `1e30`, and the function returns a huge finite distance (`1e15`) with an invalid partial path instead of signaling no feasible path. This can mislead downstream logic that interprets...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3424#discussion_r3159965157)

---

## Reviewer (google-labs-jules[bot]) (3 comments)

### PR #3424: src/shared/python/ml/dataset_generator.py:None

Actionable: Yes
Has Suggestion: No

```
Excellent point. I have removed the broad `except AttributeError` that was silently logging and swallowing errors. The engine `step` method errors will now be re-raised directly, preventing silent state corruption. Thanks for catching this!
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3424#discussion_r3160362533)

---

### PR #3424: src/shared/python/signal_toolkit/signal_processing.py:203

Actionable: Yes
Has Suggestion: No

```
Great catch. I have updated the pure python `compute_dtw_path` fallback algorithm to properly check for unreachable states `if dtw_matrix[n, m] == np.inf: return float('inf'), np.empty(0, dtype=np.int32), np.empty(0, dtype=np.int32)` instead of returning a truncated/invalid backtracking array and sentinel value. Thanks!
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3424#discussion_r3160362693)

---

### PR #3424: src/shared/python/signal_toolkit/signal_processing.py:203

Actionable: Yes
Has Suggestion: No

```
Glad that looks correct. I also noticed that the `Comment-to-Issue-Converter.yml` workflow was failing because it referenced a nonexistent label (`human-review`). I fixed this by removing the dynamic label assignment and only using `review-feedback,auto-generated`. Pushing these fixes now.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3424#discussion_r3160468906)

---

