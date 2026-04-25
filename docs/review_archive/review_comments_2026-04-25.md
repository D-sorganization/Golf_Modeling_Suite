# Review Comments Archive - 2026-04-25

Generated: 2026-04-25T02:53:51.419242

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3248: src/shared/python/dataset_generator/generator.py:154

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Use engine control dimension when sampling batch controls**

The batch generator derives control width from `len(min_v)`, but the `PhysicsEngine` contract allows actuator dimension `n_u` to differ from velocity dimension `n_v`; on engines that validate control size (for example MuJoCo checks `len(u) == model.nu`), this produces incorrectly shaped control vectors and `set_control()` fails on the first rollout....
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3248#discussion_r3141788691)

---

### PR #3248: src/shared/python/dataset_generator/generator.py:77

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Reset engine state before each generated trajectory**

`generate_trajectory()` resets only the recorder and then calls `set_state()` without resetting the engine, so any engine that preserves simulation time across `set_state` will leak clock/stateful context between runs. In `generate_batch()`, this means later runs are not independent trajectories (their recorded `times` continue from prior runs), which cor...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3248#discussion_r3141788693)

---

