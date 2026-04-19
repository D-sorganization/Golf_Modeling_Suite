# Review Comments Archive - 2026-04-18

Generated: 2026-04-18T18:41:04.357332

## Reviewer (chatgpt-codex-connector[bot]) (4 comments)

### PR #2772: src/launchers/golf_launcher.py:625

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Replace QRunnable signal with QObject-backed notifier**

`_schedule_cleanup` connects to `worker.finished`, but `ProcessCleanupWorker` inherits `QRunnable` rather than `QObject`, so its `pyqtSignal` is not a usable bound Qt signal. In PyQt this causes runtime failure when connecting/emitting (typically on the first cleanup timer tick), which disables cleanup and leaves `running_processes` stale while the UI k...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2772#discussion_r3105964989)

---

### PR #2772: src/api/task_manager.py:229

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Initialize `_closed` before creating semaphore**

`__del__` now assumes `_closed` always exists, but `_closed` is assigned only after `asyncio.Semaphore(...)`. If semaphore construction fails (for example `max_concurrent < 0`), object finalization hits `if not self._closed` and raises an `AttributeError` during garbage collection, obscuring the original constructor failure with an "Exception ignored in __del_...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2772#discussion_r3105964990)

---

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
