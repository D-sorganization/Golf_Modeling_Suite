# Review Comments Archive - 2026-04-18

Generated: 2026-04-18T18:41:04.357332

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #2774: src/shared/python/physics/impact_model/utils.py:134

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Correct expected energy-loss ratio denominator**

`validate_energy_balance()` now computes `expected_loss_factor` as `mu * (1 - e^2) / (1 + mu)^2`, but this function compares against `energy_lost / total_ke_pre`; for the modeled case (ball initially at rest), the correct fraction of pre-impact kinetic energy is `(1 - e^2) / (1 + mu)` with `mu = m_club / m_ball`. With current code, typical driver impacts are s...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2774#discussion_r3106046834)

---

### PR #2774: src/shared/python/physics/impact_model/models.py:139

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Map impact_offset into 3D before cross product**

`impact_offset` is defined as a 2D face-plane vector `[horizontal, vertical]`, but `_compute_friction_impulse_on_club()` passes it directly to `np.cross` with a 3D tangent direction. NumPy then interprets the 2D value as `[x, y, 0]`, which reassigns the horizontal face offset to the global x-axis and produces torques on incorrect axes, so club angular updates ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2774#discussion_r3106046836)

---

