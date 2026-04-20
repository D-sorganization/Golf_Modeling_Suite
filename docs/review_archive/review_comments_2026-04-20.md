# Review Comments Archive - 2026-04-20

Generated: 2026-04-20T03:38:59.265658

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #2849: tests/unit/test_drag_crisis_calibration.py:13

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Cover AerodynamicsCalculator in drag-crisis tests**

This test module claims to pin the 3-segment Cd(Re) behavior for both `aerodynamics.DragModel` and `engines.common.physics.AerodynamicsCalculator`, but it only exercises `DragModel`. As a result, changes to `AerodynamicsCalculator._compute_drag_coefficient` can drift silently while comments in `src/engines/common/physics.py` now point to this file as the gu...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2849#discussion_r3110005465)

---

