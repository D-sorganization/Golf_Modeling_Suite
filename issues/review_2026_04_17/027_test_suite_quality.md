# [CRITICAL] Test suite: mocked physics at module level, loose tolerances, tautologies, fragile fixtures

## Summary

CLAUDE.md explicitly bans `sys.modules["pydrake"] = MagicMock()` at
module level. The test suite violates this rule in multiple files and
contains numerous tests that are cosmetic rather than validating.
The result is a green CI that does not actually exercise the physics
it claims to cover.

## Findings

### 1. `sys.modules["pydrake"] = MagicMock()` at module level (CLAUDE.md violation)

Files flagged:
- `tests/unit/engines/drake/test_drake_visualizer.py:14-15`
- `tests/unit/engines/drake/test_induced_acceleration.py:13-14`
- `tests/unit/test_optimize_arm.py:16-17` (Pinocchio)
- `tests/unit/engines/mujoco/conftest.py:13-15` (MuJoCo)
- `tests/unit/engines/opensim/test_muscle_conditioning.py:37`

These tests pollute `sys.modules` for the rest of the process. Any
subsequent test that tries to import the real engine is silently
served the mock. The physics bugs in issue #013 would be caught by
many of these tests if they were not mocked out.

### 2. Cross-engine parity allows 50 % relative error

`tests/cross_engine/test_mujoco_vs_pinocchio.py:268-276` allows
`rel_error < 0.5` on mass-matrix comparison with a comment about
"different inertia conventions". No test actually measures the
inertia-convention difference; the tolerance is a catch-all.

### 3. Energy-conservation tolerances are unjustified

`tests/physics_validation/test_energy_conservation.py:83, 179` —
0.1 % for MuJoCo, 0.05 J for Pinocchio, 0.01 J for Drake. No
derivation; no convergence study on step size; Pinocchio bound is
weaker than it needs to be (and will mask the integration-order
bug in issue #014).

### 4. Aerodynamics parity uses a single speed / spin case

`tests/test_aerodynamics_parity.py:57-72, 138-157` — 1 m/s low-Re
regime and 300 rpm hardcoded. No parametric sweep; no comparison to
empirical Cd(Re) or Cl(S) curves.

### 5. Injury-risk tests use Mock() objects end-to-end

`tests/test_injury_risk.py:14-177` — all fixtures are Mocks. No
comparison to published biomechanical injury thresholds. Tests pass
regardless of whether the scoring logic is correct.

### 6. Joint-stress thresholds are unreferenced formulas

`tests/test_joint_stress.py:50-88` — checks `indicator = 50 + 110·0.5
= 105 > 100`. No citation for the formula; no biomechanics ground truth.

### 7. Ball-flight parity tests marked `xfail` on Windows

`tests/parity/test_ball_flight_parity.py:86-119` — two critical
gravity-only / drag-reduction tests disabled.

### 8. Benchmarks have no regression thresholds

`tests/benchmarks/test_performance_baseline.py:16-60`,
`tests/test_performance_benchmarks.py:64-69` — `assert result > 0`.
No baseline; `pytest-benchmark` imported but not enforced.

### 9. CI-infrastructure tests are tautologies

`tests/test_ci_infrastructure.py:20-48` — `assert np.__version__ is
not None` and the like. If numpy is installed at all, these pass.

### 10. Fixture scopes are `module` for mocks that mutate state

`tests/conftest.py:201-228` — `mock_drake_dependencies`,
`mock_mujoco_dependencies` have `scope="module"`. Mutations in one
test leak into the next. Use `scope="function"`.

### 11. Drift-control decomposition skips test when residual is large

`tests/acceptance/test_drift_control_decomposition.py:110-120` — if
residual > 10.0, test is `skip`ped instead of `fail`ed. This is
upside-down — the whole point is to flag large residuals.

### 12. Pinocchio ecosystem tests do nothing with the model

`tests/test_pinocchio_ecosystem.py:109-112` — create model, exit.
Import smoke test at best.

### 13. Rust kernel adapter has fallback-tested path

`tests/test_rust_kernel_adapter.py:43-49, 65-70` — `if isinstance(config,
dict)` chain silently falls through to Python fallback when Rust is
absent. No negative test that forces Rust and fails if absent.

### 14. Pendulum analytical test allows 20 % error

`tests/analytical/test_pendulum_lagrangian.py:79-94` — `rtol=2e-1`
on a closed-form inverse-dynamics check. A sign error would pass.

### 15. `test_drag_drop_functionality.py` (29 KB) likely GUI-rendering

`tests/test_drag_drop_functionality.py` — large GUI tests that
typically fail in headless CI. No documented xvfb strategy.

### 16. Dataclass round-trip "tests"

`tests/test_comparative_analysis.py:146-170` — creates dataclass,
checks it round-trips. Tests `__init__`, not any logic.

## Impact

CI status tells us the suite compiles and imports. It does not tell
us that the physics is correct, the parity is tight, or that the
biomechanical analyses produce meaningful numbers. Many of the bugs
in issues #013 / #014 / #015 / #020 / #025 would be caught here if
the tests were rigorous.

## Acceptance Criteria

- [ ] Remove every `sys.modules[engine] = MagicMock()` at module
      scope. Replace with `patch.dict(sys.modules, {...})` context
      managers or function-scoped fixtures (per CLAUDE.md policy).
- [ ] Parity tests: derive the expected inertia-convention delta
      from first principles and tighten tolerance to ≤ 5 %, or add a
      conversion layer so the engines agree.
- [ ] Energy-conservation tolerances: document the derivation,
      parameterize by step size, and run the convergence study in CI.
- [ ] Aerodynamics parity: parametrize over 30–80 m/s and 1000–8000 rpm;
      compare to empirical curves from the new calibration data
      (issue #016).
- [ ] Injury-risk / joint-stress: ground at least one test case in
      published biomechanical data (e.g., Han et al. 2019).
- [ ] Un-xfail the ball-flight parity tests; fix the Windows path.
- [ ] Benchmarks: set baselines in `tests/benchmarks/baselines.json`,
      fail CI on >10 % regression.
- [ ] Replace tautologies with functional checks (e.g.
      `np.array([1,2,3]).sum() == 6`).
- [ ] Change all module-scope mock fixtures to function scope.
- [ ] Drift-control residual failing threshold: fail hard on residual
      > small constant; no conditional skip.
- [ ] Pinocchio ecosystem tests: exercise at least forward-kinematics
      and inverse-dynamics, not just model creation.
- [ ] Rust kernel adapter: add a test that requires Rust and is
      `skipif` only if Rust is not available.
- [ ] Pendulum tolerance: derive from integrator order and tighten.
- [ ] Document the xvfb / offscreen Qt setup for GUI tests; mark any
      that cannot run headless with `requires_gl`.
- [ ] Replace dataclass round-trip tests with tests of derived fields.

## Related

- Every other issue in this review — the test gaps are what lets the
  bugs land.
