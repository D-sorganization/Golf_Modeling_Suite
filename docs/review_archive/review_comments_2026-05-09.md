# Review Comments Archive - 2026-05-09

Generated: 2026-05-09T16:11:25.667202

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4973: docs/development/test_coverage_epic.md:26

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Point Sprint 2 at existing physics package**

The Sprint 2 action targets `src/shared/python/physics_core/`, but that directory does not exist in this repository (the shared physics code lives under `src/shared/python/physics/`). Keeping this path in the plan will send remediation work to a non-existent module tree and can cause the coverage effort to miss the actual high-risk physics code that should be ratc...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4973#discussion_r3214013231)

---

### PR #4973: docs/development/test_coverage_epic.md:32

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Use the real API route directory in Sprint 3**

The Sprint 3 plan references `src/api/routers/`, but the codebase uses `src/api/routes/` for REST/WebSocket route modules. This mismatch makes the remediation instructions inaccurate and can derail coverage tooling/tasks that rely on path-based targeting, leaving the intended API surface under-tested.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4973#discussion_r3214013233)

---

