# Review Comments Archive - 2026-04-25

Generated: 2026-04-25T10:59:51.737100

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3279: src/shared/python/engine_core/base_physics_engine.py:487

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Provide non-breaking capabilities behavior in BasePhysicsEngine**

Making `BasePhysicsEngine.capabilities` abstract here turns every existing `BasePhysicsEngine` subclass without that override into an abstract class. In this repo, `PendulumPhysicsEngine` and `GolfSwingPendulumEngine` do not implement `capabilities()`, so instantiating them now raises `TypeError` and breaks pendulum engine usage at runtime. Th...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3279#discussion_r3142352325)

---

### PR #3279: src/engines/physics_engines/myosuite/python/myosuite_physics_engine.py:893

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Stop advertising CONTACT_FORCES in MyoSuite capabilities**

This declares `Capability.CONTACT_FORCES`, but `MyoSuitePhysicsEngine` does not implement `compute_contact_forces()`, so calls fall back to `DynamicsInterface.compute_contact_forces()` which returns `np.zeros(3)` by default. With this capability flag set, downstream code that correctly gates on `engine.capabilities()` will treat zero vectors as real ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3279#discussion_r3142352327)

---

