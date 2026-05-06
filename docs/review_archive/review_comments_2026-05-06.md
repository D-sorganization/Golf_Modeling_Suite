# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T14:41:41.980079

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #4085: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/motion_matching/shared/scripts/probe_perf.m:45

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Count flattened CSB signals directly**

`local_flatten_csb` already returns a scalar count, but this code wraps it in `numel(...)`, which always evaluates to `1` for any scalar. As a result, every run that has `CombinedSignalBus` reports `csb_signals=1`, so the benchmark output cannot distinguish logging payload size across configs and can mislead performance decisions based on this script.

Useful? React wit...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4085#discussion_r3197673927)

---

