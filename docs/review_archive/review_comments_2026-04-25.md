# Review Comments Archive - 2026-04-25

Generated: 2026-04-25T11:00:26.928822

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #3281: src/shared/python/engine_core/base_physics_engine.py:487

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Avoid making BasePhysicsEngine abstract without migrations**

Adding `@abstractmethod capabilities()` here makes every existing `BasePhysicsEngine` subclass that lacks this method non-instantiable. In this tree, `PendulumPhysicsEngine` and `GolfSwingPendulumEngine` do not implement `capabilities()`, so constructing them now raises `TypeError` (e.g., `Can't instantiate abstract class ... without an implementat...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3281#discussion_r3142352713)

---

