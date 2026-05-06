# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T15:39:31.576229

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4141: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/motion_matching/shared/prepare_fast_sim_input.m:92

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reset MaxStep when high_precision is disabled**

`prepare_fast_sim_input` only sets `MaxStep` when `opts.high_precision` is true, so when callers pass an existing `Simulink.SimulationInput` (supported by this function) and later call it with `high_precision=false`, the previous `MaxStep` value is retained. This silently keeps high-precision behavior enabled (or any prior custom `MaxStep`), which can skew perf...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4141#discussion_r3197941463)

---

### PR #4141: src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/motion_matching/shared/scripts/perf_maxstep_sweep.m:163

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Validate max_steps ordering before choosing reference run**

`perf_maxstep_sweep` assumes the first `opts.max_steps` entry is the most accurate reference and computes all RMSE/work deltas against it, but the function never enforces or sorts that ordering. If a caller provides a custom unsorted `max_steps` vector (which the API allows), the reported accuracy metrics and final recommendation become systematical...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4141#discussion_r3197941465)

---

