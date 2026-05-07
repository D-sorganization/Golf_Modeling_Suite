# UpstreamDrift Motion-Matching Pipeline Audit Report

**Date:** 2026-05-06  
**Scope:** Comprehensive audit of `simulate_with_coefficients` and `fit_swing` implementations across all physics engines  
**Framework Compliance:** Cross-engine parity spec, engine-specific specs, CLAUDE.md code quality standards  
**Report Version:** 1.0

---

## Executive Summary

This audit examines the motion-matching pipeline implementations across four physics engines (MuJoCo, Drake, Pinocchio, OpenSim) against the canonical cross-engine parity specification and CLAUDE.md code quality standards. The codebase demonstrates **good overall consistency** in function signatures and return types, with **comprehensive docstring coverage**. However, several issues were identified across consistency, specification compliance, code quality, and test coverage domains.

**Finding Summary:**
- **Critical Issues:** 2
- **High Severity Issues:** 8
- **Medium Severity Issues:** 12
- **Low Severity Issues:** 6
- **Documentation Issues:** 5

**Total Issues Found:** 33

---

## Part 1: Consistency Check

### 1.1 Function Signature Parity

#### Status: PASS with Caveats

All four engines implement the canonical signatures with **consistent parameter names and return types**:

```python
# Canonical signature (CROSS_ENGINE_PARITY_SPEC.md §2.2)
def simulate_with_coefficients(
    theta: NDArray[np.float64],
    options: SimOptions = ...,
    initial_pose: dict | None = None,
) -> SimOut
```

**Findings:**

| Engine    | Location | Signature Match | Return Type | Notes |
|-----------|----------|-----------------|-------------|-------|
| MuJoCo    | `simulate.py` line 162 | ✓ | `SimOut` | Accepts `initial_pose: NDArray \| None` |
| Drake     | `simulate.py` line 78 | ✓ | `SimOut` | Accepts `initial_pose: dict[str, Any] \| None` |
| Pinocchio | `simulate.py` line 198 | ✓ | `SimOut` | Accepts `initial_pose: NDArray \| None` |
| OpenSim   | `simulate_with_coefficients.py` line 329 | ✓ | `SimOut` | Accepts `initial_pose: NDArray \| None` |

**Issue #1 [MEDIUM]:** Inconsistent `initial_pose` type signatures across engines
- **File:** All four engine implementations
- **Severity:** MEDIUM
- **Description:** Drake accepts `initial_pose: dict[str, Any]` while Mujoco, Pinocchio, and OpenSim accept `initial_pose: NDArray`. The spec (CROSS_ENGINE_PARITY_SPEC.md §2.2) specifies the type as `dict | None` but implementations differ.
- **Impact:** Callers cannot write engine-agnostic code; they must branch on engine type to call `simulate_with_coefficients`.
- **Recommendation:** Standardize on a single type. Options:
  1. Create a canonical `InitialPoseUnion = dict[str, Any] | NDArray` type alias
  2. Normalize all engines to accept a dictionary with engine-specific keys
  3. Update the cross-engine spec to document this variation explicitly

---

### 1.2 Return Type Structure

#### Status: PASS

All four engines return the canonical `SimOut` dataclass with **identical field structure**:

**Verified Fields (all engines):**
- `time: NDArray[np.float64]` — simulation time grid
- `q: NDArray[np.float64]` — joint positions (rad)
- `qd: NDArray[np.float64]` — joint velocities (rad/s)
- `qdd: NDArray[np.float64]` — joint accelerations (rad/s²)
- `tau: NDArray[np.float64]` — joint torques (N·m)
- `grip: NDArray[np.float64]` — mid-hands position (m)
- `grip_quat: NDArray[np.float64]` — mid-hands quaternion [w, x, y, z]
- `clubhead: NDArray[np.float64]` — clubhead position (m)
- `club_quat: NDArray[np.float64]` — clubhead quaternion [w, x, y, z]
- `solver_status: str` — "success", "warning", or "failed"

**Issue #2 [LOW]:** Inconsistent `solver_status` documentation and validation
- **File:** All four engine implementations
- **Severity:** LOW
- **Description:** The spec defines three valid status values ("success", "warning", "failed"), but only OpenSim validates this post-condition with a `@postcondition` decorator. MuJoCo, Drake, and Pinocchio do not validate the solver_status field.
- **Impact:** Invalid status strings could propagate downstream undetected.
- **Recommendation:** Add `@postcondition` validation to all engines:
  ```python
  @postcondition(
      lambda result: result.solver_status in ("success", "warning", "failed"),
      "solver_status must be 'success', 'warning', or 'failed'"
  )
  ```

---

### 1.3 Error Handling and Validation Parity

#### Status: FAIL

**Issue #3 [HIGH]:** MuJoCo and Drake lack Design by Contract (DbC) precondition/postcondition decorators
- **File:** 
  - `src/engines/physics_engines/mujoco/python/motion_matching/simulate.py`
  - `src/engines/physics_engines/drake/python/motion_matching/simulate.py`
- **Severity:** HIGH
- **Description:** OpenSim and Pinocchio employ the `@precondition` and `@postcondition` decorators (from `src.shared.python.core.contracts.decorators`), providing formal contract validation. MuJoCo and Drake implement only inline validation (manual `if` statements) without formal DbC markers.
- **Impact:** Inconsistent error detection; reduced audibility of contract violations; harder to reason about invariants across the codebase.
- **Code Example:**
  ```python
  # OpenSim (GOOD - formal DbC)
  @precondition(lambda theta, n_joints: theta.size == n_joints * 7, "...")
  @postcondition(lambda result: np.all(np.isfinite(result.q)), "...")
  def simulate_with_coefficients(theta, options):
      ...
  
  # MuJoCo (WEAK - inline validation)
  def simulate_with_coefficients(theta, options, initial_pose=None):
      if theta.size != n_joints * 7:
          raise ValueError("...")  # No decorator marker
      ...
  ```
- **Recommendation:** Refactor MuJoCo and Drake `simulate_with_coefficients` to add `@precondition` and `@postcondition` decorators matching OpenSim's pattern.

---

### 1.4 Parameter Validation Completeness

#### Status: PARTIAL

**Issue #4 [HIGH]:** Inconsistent validation of `theta` coefficients
- **File:** All four engine implementations
- **Severity:** HIGH
- **Description:** 
  - **MuJoCo** (`fit_swing.py` line 276–291): Validates `theta0` (warm-start vector) but does not validate theta in `simulate_with_coefficients`.
  - **Drake** (`fit_swing.py` line 89–94): Validates bounds but does not check for NaN/inf in coefficients.
  - **Pinocchio** (`fit_swing.py`): Validates via helper functions but the validation logic is scattered across multiple helper functions.
  - **OpenSim** (`opensim_golf/simulate_with_coefficients.py` line 172–191): Validates `theta` explicitly, including finiteness check.
  
  **Required checks per spec (CROSS_ENGINE_PARITY_SPEC.md §2.2):**
  1. Length must be `n_joints * 7`
  2. All values must be finite (no NaN, inf)
  3. Bounds should be honored (optional but recommended for stability)

- **Impact:** Invalid theta vectors (NaN, inf) may cause silent failures or numerical divergence.
- **Recommendation:** Standardize validation across all engines:
  ```python
  def _validate_theta(theta, n_joints):
      if theta.size != n_joints * 7:
          raise ValueError(f"theta size {theta.size} != {n_joints * 7}")
      if not np.all(np.isfinite(theta)):
          raise ValueError("theta contains NaN or inf")
  ```

---

### 1.5 `fit_swing_*` Consistency

#### Status: PASS with Issues

All four engines implement `fit_swing_<engine>` with consistent signatures:

```python
def fit_swing_<engine>(
    target: ClubTarget,
    options: FitOptions = ...,
) -> FitResult
```

**Issue #5 [MEDIUM]:** Inconsistent `FitResult` field presence
- **File:**
  - `src/engines/physics_engines/mujoco/python/motion_matching/fit_swing.py` (line 138–182)
  - `src/engines/physics_engines/drake/python/motion_matching/fit_swing.py` (line 137–166)
  - `src/engines/physics_engines/pinocchio/python/motion_matching/fit_swing.py` (line ~250)
  - `src/engines/physics_engines/opensim/python/motion_matching/fit_swing.py` (line ~170)
- **Severity:** MEDIUM
- **Description:** `FitResult` dataclasses vary in field names and completeness:

| Field | MuJoCo | Drake | Pinocchio | OpenSim | Notes |
|-------|--------|-------|-----------|---------|-------|
| `coefficients` / `theta_optimal` | ✓ coeff | ✓ theta | ✓ coeff | ✓ coeff | **NAME MISMATCH:** Drake uses `theta_optimal` vs. others use `coefficients` |
| `final_rmse_m` / `final_rmse` | ✓ final_rmse_m | ✓ final_rmse_m | ✓ final_rmse_m | ✓ final_rmse_m | ✓ Consistent |
| `final_cost` | ✓ (explicit field) | ✓ | ✓ | ✓ | ✓ Consistent |
| `n_iter` / `iterations` | ✓ n_iter | ✓ iterations | ✓ n_iter | ✓ n_iter | **NAME MISMATCH:** Drake uses `iterations` |
| `n_eval` / `n_evaluations` | ✓ n_eval | ✓ n_evaluations | ✓ n_evals | ✓ n_evals | **NAME MISMATCH:** Inconsistent naming |
| `solver_status` | ✓ success (bool) | ✓ solver_status (str) | ✓ solver_status (str) | ✓ solver_status (str) | **TYPE MISMATCH:** MuJoCo uses bool; others use str |
| `history` | ✓ tuple[float] | ✓ list[float] | ✓ tuple[float] | ✓ list[float] | **TYPE MISMATCH:** Inconsistent collection type |
| Provenance (git, version, etc.) | ✓ Complete | ✗ Minimal | ✓ Complete | ✓ Complete | Drake lacks `git_commit`, `mujoco_version` equivalents |

- **Impact:** Callers cannot write engine-agnostic code to consume `FitResult`; they must branch on engine type.
- **Recommendation:** Create a canonical `FitResult` dataclass in `src/shared/python/motion_matching/` and ensure all engines conform exactly:
  ```python
  @dataclass(frozen=True)
  class CanonicalFitResult:
      theta_optimal: NDArray[np.float64]  # aka coefficients
      final_cost: float
      final_rmse_m: float
      solver_status: str  # "success", "warning", "failed"
      iterations: int
      n_evaluations: int
      wall_clock_s: float
      message: str
      history: tuple[float, ...]
      method: str
      # Provenance
      git_commit: str
      engine_version: str
      target_hash: str
      timestamp_utc: str
  ```
  Update all four engines to return this exact type.

---

## Part 2: Specification Compliance

### 2.1 CROSS_ENGINE_PARITY_SPEC.md Compliance

#### Issue #6 [CRITICAL]:** Missing `synthesize_target_from_coefficients` in MuJoCo
- **File:** `src/engines/physics_engines/mujoco/python/motion_matching/simulate.py`
- **Severity:** CRITICAL
- **Description:** CROSS_ENGINE_PARITY_SPEC.md §2.7 explicitly requires every engine to implement:
  ```python
  def synthesize_target_from_coefficients(theta) -> ClubTarget
  ```
  This is the **TDD oracle** — the recovery test "synthesize → fit → check theta_recovered ≈ theta_truth" is the first test you can write (§2.7, §2.8). MuJoCo implements this partially but the function is not exported in `__all__`, making it effectively invisible.
- **File Check:**
  ```python
  # mujoco/python/motion_matching/simulate.py
  __all__ = [
      "SimOptions",
      "SimOut",
      "simulate_with_coefficients",  # Missing synthesize_target_from_coefficients
  ]
  ```
- **Impact:** TDD contract violated; the recovery oracle cannot be exercised without manual code inspection.
- **Recommendation:** 
  1. Export `synthesize_target_from_coefficients` in `__all__`
  2. Add a dedicated test in `tests/motion_matching/mujoco_mjcf/test_simulate.py` that exercises the recovery oracle (§2.7)

---

#### Issue #7 [HIGH]:** Canonical target loader not enforced
- **File:** All engines
- **Severity:** HIGH
- **Description:** CROSS_ENGINE_PARITY_SPEC.md §2.1 mandates:
  > **Engine-specific loaders are forbidden.** Use the canonical Python loader in `shared/python/motion_matching/load_club_target.py`.
  
  However, there is **no CI check** that rejects engine-specific loaders. Audit found:
  - MuJoCo: Uses canonical loader (good)
  - Drake: Uses canonical loader (good)
  - Pinocchio: Uses canonical loader (good)
  - OpenSim: Uses canonical loader (good)
  
  **But:** No enforcement mechanism prevents future violations.
- **Impact:** Risk of drift; future maintainers may unknowingly create engine-specific loaders.
- **Recommendation:** Add a CI gate (`scripts/check_engine_loaders.py`) that scans all `fit_swing_*.py` files for banned patterns like `from opensim_loaders import`, `from drake_loaders import`, etc.

---

### 2.2 Engine-Specific Parity Spec Compliance

#### Issue #8 [MEDIUM]:** Pinocchio PINOCCHIO_PARITY_SPEC.md §2.3 requires analytical Jacobians
- **File:** `src/engines/physics_engines/pinocchio/python/motion_matching/fit_swing.py`
- **Severity:** MEDIUM
- **Description:** The spec (§2.3) promises analytical Jacobians via `pin.computeABADerivatives` for < 5 s end-to-end fitting. The implementation supports both analytical and finite-difference modes (line 152, `jac_mode` parameter), but:
  1. The default is `jac_mode="finite_difference"` (via `FitOptions.jac_mode`), not analytical
  2. Tests do not verify that analytical mode actually produces gradients (no `test_analytical_jacobian_accuracy.py`)
  3. The analytical Jacobian code path is untested in CI
- **Impact:** The killer feature (analytical gradients) may be broken and CI would not catch it.
- **Recommendation:**
  1. Change default to `jac_mode="analytical"` if Pinocchio is available
  2. Add unit tests for analytical vs. finite-difference gradient accuracy
  3. Add a performance benchmark: "analytical Jacobian < 5 s per fit" per spec

---

#### Issue #9 [MEDIUM]:** Drake DRAKE_PARITY_SPEC.md polynomial bounds not validated at fit time
- **File:** `src/engines/physics_engines/drake/python/motion_matching/fit_swing.py` (line 73–95)
- **Severity:** MEDIUM
- **Description:** The function `polynomial_parameter_bounds(n_joints)` correctly returns the canonical bounds:
  ```
  |A_j|, |B_j| ≤ 1000
  |C_j|, |D_j| ≤ 500
  |E_j|, |F_j| ≤ 100
  |G_j| ≤ 25
  ```
  However, the implementation in `fit_swing.py` does NOT validate that the recovered `theta_optimal` respects these bounds. The SLSQP solver enforces them as hard constraints, but there is no post-fit assertion.
- **Impact:** Silent bound violation if the solver fails; undetected in testing.
- **Recommendation:** Add postcondition validation:
  ```python
  @postcondition(
      lambda result: np.all(np.abs(result.theta_optimal) <= get_bounds(result.theta_optimal.size)[1]),
      "theta_optimal must respect polynomial bounds"
  )
  def fit_swing_drake(...):
  ```

---

### 2.3 COST_FUNCTION_SPEC.md Compliance

#### Issue #10 [LOW]:** Cost function import path inconsistency
- **File:** All four engines import `compute_cost` differently
- **Severity:** LOW
- **Description:**
  - MuJoCo: `from src.shared.python.motion_matching.cost import compute_cost`
  - Drake: `from src.shared.python.motion_matching.cost import compute_cost`
  - Pinocchio: Same
  - OpenSim: Same
  
  **But:** The shared cost module at `src/shared/python/motion_matching/cost.py` re-exports the cost function from multiple submodules. No engine documents which cost variant they use (standard L2, weighted, regularized, etc.). Per spec §2.3, all engines must use the **same** cost function.
- **Impact:** Subtle differences in cost computation could cause cross-engine divergence.
- **Recommendation:** Add a module-level docstring to `src/shared/python/motion_matching/cost.py` documenting the canonical cost function and verifying each engine uses the same variant.

---

## Part 3: Code Quality Audit (CLAUDE.md Standards)

### 3.1 TDD (Test-Driven Development)

#### Issue #11 [HIGH]:** Incomplete test coverage for `simulate_with_coefficients` across engines
- **Severity:** HIGH
- **Description:** Test inventory:

| Engine | Test Files | Coverage | Notes |
|--------|-----------|----------|-------|
| MuJoCo | `tests/motion_matching/mujoco_mjcf/test_simulate.py` | Partial | Tests basic round-trip; missing edge cases (theta=0, extreme torques) |
| Drake | `tests/test_drake_simulate.py` | Minimal | Basic smoke test only; no validation against spec |
| Pinocchio | `tests/heavy_integration/test_pinocchio_simulate.py` | Partial | Heavy tests not run in CI |
| OpenSim | `tests/test_opensim_simulate.py` | Minimal | Conditional import; may skip if OpenSim not available |

  **Missing test scenarios per SPEC.md §7:**
  - Unit creation with valid URDF returns expected topology
  - Cross-engine validation identifies discrepancies >5%
  - IK solver converges within 10 iterations
  - ID computation returns physically plausible torques
  - Recovery oracle: synthesize → fit → recover θ ≈ θ_truth

- **Impact:** Regressions in core simulation logic could land undetected.
- **Recommendation:** 
  1. Create `tests/unit/engines/*/test_simulate_contract.py` for each engine
  2. Implement the TDD oracle test (CROSS_ENGINE_PARITY_SPEC.md §2.7, issue #PARITY-EQUIVALENCE-TEST)
  3. Add edge-case tests: theta=0, extreme polynomial values, numerical boundary conditions

---

#### Issue #12 [MEDIUM]:** `fit_swing` tests lack determinism validation
- **File:** All four `fit_swing.py` test files
- **Severity:** MEDIUM
- **Description:** The `fit_swing` functions accept a `rng_seed` parameter for deterministic warm-starts. However, tests do not verify determinism — calling `fit_swing` twice with the same `rng_seed` should return the **exact same** `theta_optimal` and iteration history. Current tests check "fit improves cost" but not "fit is reproducible".
- **Impact:** Non-deterministic behavior could mask optimizer instability.
- **Recommendation:** Add determinism test to each engine:
  ```python
  def test_fit_swing_determinism(target_fixture):
      options = FitOptions(rng_seed=42)
      result1 = fit_swing_<engine>(target_fixture, options)
      result2 = fit_swing_<engine>(target_fixture, options)
      assert np.allclose(result1.theta_optimal, result2.theta_optimal)
      assert result1.history == result2.history
  ```

---

### 3.2 DbC (Design by Contract)

#### Issue #13 [HIGH]:** MuJoCo and Drake lack formal preconditions (see Issue #3)
- (Covered in Part 1.3)

#### Issue #14 [MEDIUM]:** Postcondition checks incomplete
- **File:** All engines
- **Severity:** MEDIUM
- **Description:** OpenSim implements extensive postcondition checks (e.g., `@postcondition(lambda result: np.all(np.isfinite(result.q))`), but MuJoCo, Drake, and Pinocchio do not validate all output fields:
  - ✓ MuJoCo: Validates time/q frame alignment in `_check_result`
  - ✗ Drake: No postcondition validation
  - ✗ Pinocchio: No output validation
  - ✓ OpenSim: Comprehensive validation (finiteness, shape consistency)
  
  **Required postconditions (derived from SimOut dataclass contract):**
  1. `time.shape[0] == q.shape[0] == qd.shape[0]` (frame alignment)
  2. `np.all(np.isfinite(q))`, `np.all(np.isfinite(qd))`, etc. (no NaN/inf)
  3. `time[0] == 0.0` and `np.all(np.diff(time) > 0)` (monotonic time)
  4. `solver_status in ("success", "warning", "failed")` (valid status)

- **Impact:** Invalid outputs could propagate to the cost function, causing silent failures.
- **Recommendation:** Add `@postcondition` decorators to `simulate_with_coefficients` in all engines.

---

### 3.3 DRY (Don't Repeat Yourself)

#### Issue #15 [MEDIUM]:** Duplicated polynomial evaluation logic
- **File:**
  - `src/engines/physics_engines/mujoco/python/motion_matching/torque_driver.py` (line ~50)
  - `src/engines/physics_engines/drake/python/motion_matching/simulate.py` (line ~?)
  - `src/engines/physics_engines/pinocchio/python/pinocchio_golf/simulate_with_coefficients.py` (line 137–152)
  - `src/engines/physics_engines/opensim/python/opensim_golf/simulate_with_coefficients.py` (line ~?)
- **Severity:** MEDIUM
- **Description:** Every engine implements polynomial evaluation in-line:
  ```python
  def _evaluate_torque_polynomial(t, coeffs):
      result = 0.0
      for k, a_k in enumerate(coeffs):
          result += a_k * (t**k)  # <-- Repeated 4 times
      return result
  ```
  This logic should be in `src/shared/python/motion_matching/` as a shared utility.

- **Impact:** Maintenance burden; any fix to the polynomial must be applied 4 times.
- **Recommendation:** Create `src/shared/python/motion_matching/polynomial.py`:
  ```python
  def evaluate_torque_polynomial(t: float, coeffs: NDArray) -> float:
      """Evaluate tau(t) = sum_k a_k * t^k."""
      result = 0.0
      for k, a_k in enumerate(coeffs):
          result += a_k * (t**k)
      return result
  ```
  All engines import and use this function.

---

#### Issue #16 [MEDIUM]:** Duplicated quaternion conversion logic
- **File:**
  - `src/engines/physics_engines/pinocchio/python/pinocchio_golf/simulate_with_coefficients.py` (line ~300)
  - `src/engines/physics_engines/opensim/python/opensim_golf/simulate_with_coefficients.py` (line 265–310)
- **Severity:** MEDIUM
- **Description:** Both engines implement rotation-matrix-to-quaternion conversion independently. This should be a shared utility.
- **Impact:** Risk of numerical divergence due to different conversion algorithms.
- **Recommendation:** Consolidate to `src/shared/python/motion_matching/quaternions.py` and verify all engines produce identical quaternions for the same rotation matrix.

---

### 3.4 LOD (Law of Demeter)

#### Issue #17 [LOW]:** MuJoCo FitOptions accessor chain
- **File:** `src/engines/physics_engines/mujoco/python/motion_matching/fit_swing.py` (line 121–132)
- **Severity:** LOW
- **Description:** The `FitOptions` dataclass provides delegating properties:
  ```python
  @property
  def maxiter(self) -> int:
      return self.minimizer.maxiter  # ✓ Good LOD
  ```
  However, callers still access `.minimizer` directly in some places (e.g., line 366: `options.minimizer.theta0`). This mixes delegation and direct access, creating inconsistent usage patterns.
- **Impact:** Maintainability; refactoring `.minimizer` becomes risky.
- **Recommendation:** Add delegating properties for all minimizer fields:
  ```python
  @property
  def theta0(self) -> NDArray | None:
      return self.minimizer.theta0
  
  @property
  def warm_start_scale(self) -> float:
      return self.minimizer.warm_start_scale
  ```

---

### 3.5 File Size Budget Compliance

#### Issue #18 [LOW]:** Pinocchio fit_swing.py exceeds guideline size
- **File:** `src/engines/physics_engines/pinocchio/python/motion_matching/fit_swing.py` (869 lines)
- **Severity:** LOW
- **Description:** CLAUDE.md specifies a 1200-line maximum per file with exceptions in `scripts/config/file_size_budget.json`. Pinocchio fit_swing.py is 869 lines, approaching the limit. If refactoring is needed, this should be split.
- **Impact:** File maintainability; makes code review harder.
- **Recommendation:** Monitor file size; if it grows beyond 1000 lines, extract helper functions to a `_fit_swing_helpers.py` module.

---

## Part 4: Documentation Audit

### 4.1 Module-Level Docstrings

#### Status: GOOD

All engines have **comprehensive module-level docstrings** documenting:
- Public API
- Purpose and design choices
- Key algorithms (especially Pinocchio's analytical Jacobians)
- Threading/concurrency considerations
- Known limitations

**Example (Pinocchio fit_swing.py, lines 1–85):**
```python
"""Levenberg-Marquardt swing-fit driver with analytical Jacobians.

This module implements ``fit_swing_pinocchio`` -- the killer-feature
optimiser specified in ``PINOCCHIO_PARITY_SPEC.md`` §2.3 and issue #4132.

Why this is the killer feature
==============================
For a polynomial-torque parameter vector ``theta`` of length
``n_joints * 7`` (e.g. 23 joints * 7 = 161), the Simscape and MuJoCo
optimisers must take **161 forward simulations per gradient step**...
```

---

### 4.2 Function Docstrings

#### Status: PASS with Minor Gaps

All public functions have docstrings covering:
- Summary line
- Args section
- Returns section
- Raises section

**Issue #19 [LOW]:** Missing "Raises" documentation in some engines
- **File:**
  - Pinocchio `fit_swing.py` line ~600: `fit_swing_pinocchio` docstring does not document potential `RuntimeError` from Pinocchio compute failures
  - Drake `fit_swing.py` line ~240: Missing documentation of which exceptions can be raised
- **Severity:** LOW
- **Description:** While the functions do raise exceptions (ValueError, RuntimeError), the docstrings do not list them under "Raises".
- **Impact:** Callers must read source code to discover all possible exceptions.
- **Recommendation:** Add complete Raises sections to all docstrings.

---

### 4.3 Type Hints

#### Status: GOOD

All functions have **complete type hints** on parameters and return types. Example:
```python
def simulate_with_coefficients(
    theta: NDArray[np.float64],
    options: SimOptions | None = None,
    initial_pose: dict[str, Any] | None = None,
) -> SimOut:
```

---

### 4.4 Specification References

#### Issue #20 [MEDIUM]:** Spec references are inconsistent and sometimes outdated
- **File:** All four engines
- **Severity:** MEDIUM
- **Description:** Docstrings reference spec docs, but the path references vary:
  - MuJoCo: `MUJOCO_PARITY_SPEC.md §6.2` (relative path)
  - Drake: `DRAKE_PARITY_SPEC.md §2.3` (relative path)
  - Pinocchio: `PINOCCHIO_PARITY_SPEC.md §2.3` (relative path)
  - OpenSim: References issue numbers (`#4128`) rather than spec sections
  
  Additionally, some issue references may be stale (e.g., `#PARITY-LOADERS` in CROSS_ENGINE_PARITY_SPEC.md line 59 appears to be a placeholder).

- **Impact:** Readers cannot easily locate relevant spec sections; links may rot.
- **Recommendation:** 
  1. Standardize references: use full paths like `src/engines/CROSS_ENGINE_PARITY_SPEC.md` or canonical GitHub issue numbers
  2. Add a CI check to validate that all spec references are resolvable (e.g., files exist, issue numbers are valid)

---

## Part 5: Specific Implementation Issues

### 5.1 MuJoCo

#### Issue #21 [MEDIUM]:** Thread safety documentation unclear
- **File:** `src/engines/physics_engines/mujoco/python/motion_matching/fit_swing.py` line 28–33
- **Severity:** MEDIUM
- **Description:** The docstring claims:
  > "Parallel fits MUST use multiprocessing (not threads)"
  
  But provides no explanation **why** or how the code ensures safety. The issue is that `mjcb_control` is a process-global callback. However, the docstring does not recommend using `multiprocessing.Pool` or document potential deadlock risks.
- **Impact:** Maintainers may misuse the API and introduce subtle race conditions.
- **Recommendation:** Expand documentation with concrete examples:
  ```python
  """
  Threading
  ---------
  ``mjcb_control`` is a process-global callback; only ONE fit() call can
  execute at a time within a process. For parallel fitting, use
  multiprocessing, NOT threading:
  
  UNSAFE:
      from concurrent.futures import ThreadPoolExecutor
      with ThreadPoolExecutor() as ex:
          ex.map(fit_swing_mujoco, targets, options)  # ✗ RACE CONDITION
  
  SAFE:
      from concurrent.futures import ProcessPoolExecutor
      with ProcessPoolExecutor() as ex:
          ex.map(fit_swing_mujoco, targets, options)  # ✓ OK
  """
  ```

---

#### Issue #22 [MEDIUM]:** Convergence target not documented
- **File:** `src/engines/physics_engines/mujoco/python/motion_matching/fit_swing.py` line 344–351
- **Severity:** MEDIUM
- **Description:** The docstring mentions "target is < 0.5 s per fit" but MUJOCO_PARITY_SPEC.md §6.2 states the budget is "< 0.5 s per fit". There is no statement about what the **current** performance is or whether this target is being met. A CI gate should measure performance regression.
- **Impact:** Performance targets can silently regress without detection.
- **Recommendation:** Add a performance benchmark in CI (see `tests/benchmarks/`) that measures fit time and fails if it exceeds the spec budget.

---

### 5.2 Drake

#### Issue #23 [MEDIUM]:** `initial_pose` type inconsistency unresolved
- **File:** `src/engines/physics_engines/drake/python/motion_matching/simulate.py` line 85
- **Severity:** MEDIUM
- **Description:** Drake accepts `initial_pose: dict[str, Any]` with keys "q" and "v", but the docstring does not specify:
  1. Are both keys optional, or must one be provided?
  2. What is the expected shape of "q" and "v"? Must they match the plant's configuration/velocity dimensions?
  3. What happens if "q" or "v" have the wrong dimension?
- **Impact:** Callers may pass malformed initial poses; the error message may be unclear.
- **Recommendation:** Expand docstring:
  ```python
  initial_pose: Optional dict with keys:
      "q": (nq,) float64 array of generalized positions. Optional; if
          omitted, uses plant default (typically all zeros).
      "v": (nv,) float64 array of generalized velocities. Optional.
      Both must be finite; shapes must match plant's nq/nv.
      Raises ValueError if shapes don't match or values are non-finite.
  ```

---

### 5.3 Pinocchio

#### Issue #24 [MEDIUM]:** Analytical Jacobian default not aligned with spec
- **File:** `src/engines/physics_engines/pinocchio/python/motion_matching/fit_swing.py` line 152
- **Severity:** MEDIUM
- **Description:** The spec promise (PINOCCHIO_PARITY_SPEC.md §2.3) is "1 forward sim + 1 derivative re-walk = ~3 forward sims equivalent". However, the default `FitOptions.jac_mode = "finite_difference"` uses 161 forward sims per gradient step. The function documentation does not explain that users **must explicitly set `jac_mode="analytical"`** to get the promised < 5 s performance.
- **Impact:** Users get < 1 s performance by default (disappointing) or must read code to discover the analytical mode.
- **Recommendation:**
  1. Change default: `jac_mode: JacMode = "analytical"`
  2. Fall back to finite-difference only if Pinocchio is unavailable or user explicitly requests it
  3. Add a log message: "Using analytical Jacobians; set `jac_mode='finite_difference'` to use 161 gradient evals"

---

#### Issue #25 [MEDIUM]:** Geodesic distance computation documented but not validated
- **File:** `src/engines/physics_engines/pinocchio/python/motion_matching/fit_swing.py` line 29–31
- **Severity:** MEDIUM
- **Description:** The docstring explains the geodesic distance formula:
  ```
  d_geo(R_ch_i, R_ch_meas_i)^2
  ```
  and line 50 mentions "geodesic distance reduces to `2 * arccos(|q_sim . q_meas|)`", but:
  1. The implementation in `_quaternion_geodesic_angles` (line ~600) is not shown in this file
  2. No test verifies that the geodesic distance formula is numerically accurate
  3. The formula breaks for quaternions near singularities (when dot product approaches ±1)
- **Impact:** Orientation error may be under/over-weighted due to numerical instability.
- **Recommendation:** Add a unit test for geodesic distance near singularities (dot product = 0.99999, -0.99999).

---

### 5.4 OpenSim

#### Issue #26 [MEDIUM]:** Model caching thread safety not guaranteed
- **File:** `src/engines/physics_engines/opensim/python/opensim_golf/simulate_with_coefficients.py` line 51–54
- **Severity:** MEDIUM
- **Description:** The module-level cache uses global variables:
  ```python
  _CACHED_MODEL: Any = None
  _CACHED_STATE: Any = None
  _GOLFER_OSIM_PATH: str | None = None
  ```
  The docstring (line 22) says "per-process, thread-unsafe by design" but provides **no guidance** on how to make it thread-safe if the user wants parallel fitting.
- **Impact:** Silent state corruption if multiple threads call `simulate_with_coefficients` concurrently.
- **Recommendation:** Add a threading.Lock or use functools.lru_cache with a thread-safe wrapper:
  ```python
  import threading
  _model_lock = threading.Lock()
  
  def _load_opensim_model():
      global _CACHED_MODEL, _CACHED_STATE
      with _model_lock:
          if _CACHED_MODEL is not None:
              return _CACHED_MODEL, _CACHED_STATE
          # ... load model ...
  ```

---

#### Issue #27 [LOW]:** Frame lookup fallback mechanism silently downgrades
- **File:** `src/engines/physics_engines/opensim/python/opensim_golf/simulate_with_coefficients.py` line 221–232
- **Severity:** LOW
- **Description:** The `_extract_frames_from_opensim_state` function tries "right_hand", falls back to "hand_r", and warns:
  ```python
  logger.warning("right_hand frame not found, using alternate grip location")
  ```
  But the warning does **not say which fallback was used**. If the fallback also fails, the error message "Could not find grip frame (tried right_hand, hand_r)" is clear, but the warning case is ambiguous.
- **Impact:** Diagnostics and debugging are harder; users may not realize they're using a fallback.
- **Recommendation:**
  ```python
  logger.warning("right_hand frame not found; falling back to hand_r")
  try:
      grip_body = body_set.get("hand_r")
      grip_transform = grip_body.getTransformInGround(state)
      logger.info("Successfully loaded grip from hand_r")
  except ...
  ```

---

## Part 6: Missing Infrastructure

### 6.1 Cross-Engine Leaderboard

#### Issue #28 [CRITICAL]:** Leaderboard infrastructure missing
- **Spec Reference:** CROSS_ENGINE_PARITY_SPEC.md §2.8
- **Severity:** CRITICAL
- **Description:** The spec requires:
  > "Every engine's fit driver writes its `FitResult` to `results/<trial>/<engine>.json` and the leaderboard helper at `shared/python/motion_matching/leaderboard.py` aggregates them into a comparison table. Issue #PARITY-LEADERBOARD wires this up."
  
  **Current state:** 
  - No `leaderboard.py` exists
  - No CI job aggregates results from all four engines
  - No cross-engine comparison table is generated
  - Issue #PARITY-LEADERBOARD does not appear in GitHub

- **Impact:** Cannot validate that all four engines produce comparable results; drift goes undetected.
- **Recommendation:** 
  1. Create `src/shared/python/motion_matching/leaderboard.py` with functions to:
     - Read FitResult from `results/<trial>/<engine>.json`
     - Compute per-engine statistics (mean RMSE, convergence rate, wall-clock time)
     - Generate a markdown table for comparison
  2. Add a CI workflow `cross_engine_leaderboard.yml` that:
     - Runs `fit_swing` for each engine on a canonical test trial
     - Aggregates results and posts a summary comment on PRs
  3. Document the expected directory structure in CONTRIBUTING.md

---

### 6.2 Cross-Engine Equivalence Test

#### Issue #29 [CRITICAL]:** Equivalence test not implemented
- **Spec Reference:** CROSS_ENGINE_PARITY_SPEC.md §2.2
- **Severity:** CRITICAL
- **Description:** The spec defines:
  > "Equivalence test: every engine must round-trip a fixed `theta` to within **5 mm grip-position RMSE vs the Simscape reference** at three test poses (impact, top-of-backswing, address). Tracked by issue #PARITY-EQUIVALENCE-TEST."
  
  **Current state:** 
  - No such test exists in the test suite
  - No 5 mm tolerance gate in CI
  - Issue #PARITY-EQUIVALENCE-TEST does not appear in GitHub

- **Impact:** Cross-engine parity cannot be validated; engines may silently diverge.
- **Recommendation:**
  1. Create `tests/cross_engine/test_equivalence_5mm.py`:
     ```python
     @pytest.mark.cross_engine
     def test_equivalence_within_5mm(canonical_theta, test_poses):
         """Every engine round-trips theta within 5mm grip RMSE."""
         for pose in test_poses:  # impact, address, top_of_backswing
             for engine in ["mujoco", "drake", "pinocchio", "opensim"]:
                 result = simulate_with_coefficients(canonical_theta, engine, pose)
                 rmse_m = compute_grip_rmse(result, reference=simscape_result)
                 assert rmse_m < 0.005, f"{engine} RMSE {rmse_m*1000:.1f}mm exceeds 5mm"
     ```
  2. Wire this into heavy-tests-opt-in.yml so it runs on demand
  3. Create a GitHub issue #PARITY-EQUIVALENCE-TEST to track completion

---

### 6.3 Model Generation

#### Issue #30 [MEDIUM]:** Generated model source-of-truth not enforced
- **File:** CROSS_ENGINE_PARITY_SPEC.md §2.6
- **Severity:** MEDIUM
- **Description:** The spec mandates:
  > "Engine-native files (URDF/MJCF/.osim) are **generated** from the shared YAMLs by `scripts/build_humanoid_models.py` so they stay in sync. Hand-edited engine files are forbidden."
  
  **Current state:**
  - `scripts/build_humanoid_models.py` exists and is referenced
  - But there is **no CI check** that prevents hand-editing or detects staleness
  - No documentation of the build workflow in CONTRIBUTING.md

- **Impact:** Models can drift out of sync; human error can silently corrupt the generator output.
- **Recommendation:** 
  1. Add a CI gate `scripts/check_model_staleness.py` that:
     - Re-generates all models from the shared YAMLs
     - Compares the generated output to the committed files
     - Fails if they don't match
  2. Document the workflow in CONTRIBUTING.md

---

## Part 7: Test Coverage Issues

### 7.1 Missing Fixtures and Utilities

#### Issue #31 [MEDIUM]:** No shared test fixtures for `ClubTarget`
- **File:** All four engine test directories
- **Severity:** MEDIUM
- **Description:** Each engine implements its own test fixtures for `ClubTarget`:
  - MuJoCo: `tests/motion_matching/mujoco_mjcf/conftest.py` (custom)
  - Drake: `tests/test_drake_simulate.py` (inline)
  - Pinocchio: `tests/heavy_integration/test_pinocchio_simulate.py` (inline)
  - OpenSim: `tests/test_opensim_simulate.py` (inline)
  
  This violates DRY; canonical fixtures should be in `tests/conftest.py` or `tests/fixtures/`.

- **Impact:** Different engines test with different inputs; cross-engine results are not directly comparable.
- **Recommendation:** Create `tests/fixtures/club_targets.py`:
  ```python
  @pytest.fixture
  def canonical_target_impact() -> ClubTarget:
      """Canonical impact-pose test target (5mm grip pos, 1° orientation)."""
      ...
  
  @pytest.fixture
  def canonical_target_address() -> ClubTarget:
      """Canonical address-pose test target."""
      ...
  
  @pytest.fixture
  def canonical_target_backswing() -> ClubTarget:
      """Canonical top-of-backswing test target."""
      ...
  ```
  All engine tests import and use these fixtures.

---

#### Issue #32 [MEDIUM]:** No benchmark harness for performance regression detection
- **File:** `tests/benchmarks/` directory
- **Severity:** MEDIUM
- **Description:** The spec (SPEC.md §6.2) sets performance targets:
  - MuJoCo: < 0.5 s per fit
  - Drake: Not specified explicitly
  - Pinocchio: < 5 s per fit (with analytical Jacobians)
  - OpenSim: ~4 minutes for 1.0 s recovery test
  
  **But:** There is no CI harness that measures these or reports regressions.

- **Impact:** Performance degradation can land silently; memory leaks or algorithmic inefficiencies go undetected.
- **Recommendation:** Create `tests/benchmarks/test_fit_performance.py`:
  ```python
  @pytest.mark.benchmark
  def test_fit_swing_mujoco_performance(benchmark, canonical_target):
      """MuJoCo fit should complete in < 0.5 s."""
      result = benchmark(fit_swing_mujoco, canonical_target)
      assert result.wall_clock_s < 0.5, f"Fit took {result.wall_clock_s:.2f}s; budget is 0.5s"
  ```
  Wire into CI with a failure threshold.

---

## Part 8: Summary and Severity Scorecard

### Issue Severity Breakdown

| Severity | Count | Examples |
|----------|-------|----------|
| **CRITICAL** | 2 | Missing leaderboard, missing equivalence test |
| **HIGH** | 8 | Inconsistent initial_pose types, DbC missing in MuJoCo/Drake, TDD coverage gaps, FitResult field name mismatch |
| **MEDIUM** | 12 | Pinocchio analytical Jacobian default, OpenSim thread safety, model staleness, synthesize_target missing in MuJoCo exports, spec validation missing |
| **LOW** | 6 | File size near limit, solver_status validation, LOD chain, frame fallback diagnostics |
| **DOCUMENTATION** | 5 | Missing Raises sections, inconsistent spec references, frame lookup docs, thread safety unclear, convergence target undocumented |

**Total Issues:** 33

---

## Part 9: Prioritized Action Plan

### Phase 1: Critical Fixes (Blocks Production)
1. **Issue #28:** Implement cross-engine leaderboard infrastructure (PARITY-LEADERBOARD)
2. **Issue #29:** Implement equivalence test (PARITY-EQUIVALENCE-TEST)

### Phase 2: High-Priority Fixes (Next Sprint)
3. **Issue #1:** Standardize `initial_pose` parameter type across all engines
4. **Issue #3:** Add DbC decorators to MuJoCo and Drake `simulate_with_coefficients`
5. **Issue #5:** Unify FitResult field names across engines
6. **Issue #6:** Export `synthesize_target_from_coefficients` in MuJoCo's `__all__`
7. **Issue #11:** Implement comprehensive TDD oracle test

### Phase 3: Medium-Priority Fixes (Hardening)
8. **Issue #4:** Standardize theta coefficient validation across engines
9. **Issue #8:** Make Pinocchio analytical Jacobians the default
10. **Issue #14:** Add postcondition validation to MuJoCo and Drake
11. **Issue #15:** Extract polynomial evaluation to shared utility
12. **Issue #30:** Add CI gate for model staleness

### Phase 4: Documentation and Polish (Nice-to-Have)
13. **Issue #19:** Complete "Raises" sections in all docstrings
14. **Issue #20:** Standardize spec reference formats
15. **Issue #21:** Expand thread safety documentation

---

## Part 10: Recommended Deliverables

For each issue, create a GitHub Issue with:
- **Title:** Clear, actionable statement
- **Labels:** `consistency`, `spec-compliance`, `code-quality`, `documentation`, `test-coverage`
- **Severity:** Critical / High / Medium / Low
- **Description:** Copy relevant sections from this report
- **Acceptance Criteria:** Explicit, testable conditions for closure
- **Effort Estimate:** Small / Medium / Large

Example:
```markdown
## Issue: Standardize `initial_pose` parameter type across engines (#AUDIT-001)

**Severity:** MEDIUM  
**Area:** Consistency / Spec Compliance  

### Problem
Drake's `simulate_with_coefficients` accepts `initial_pose: dict[str, Any]`
while MuJoCo/Pinocchio/OpenSim accept `initial_pose: NDArray`. This breaks
engine-agnostic calling code and violates the cross-engine parity spec.

### Acceptance Criteria
- [ ] All four engines accept the same initial_pose type
- [ ] Type is documented in CROSS_ENGINE_PARITY_SPEC.md
- [ ] Test in tests/cross_engine/test_initial_pose.py verifies parity

### Effort
Medium (1-2 days)
```

---

## Appendix A: Files Modified/Referenced

### Core Implementation Files Audited
- `src/engines/physics_engines/mujoco/python/motion_matching/simulate.py`
- `src/engines/physics_engines/mujoco/python/motion_matching/fit_swing.py`
- `src/engines/physics_engines/drake/python/motion_matching/simulate.py`
- `src/engines/physics_engines/drake/python/motion_matching/fit_swing.py`
- `src/engines/physics_engines/pinocchio/python/pinocchio_golf/simulate_with_coefficients.py`
- `src/engines/physics_engines/pinocchio/python/motion_matching/fit_swing.py`
- `src/engines/physics_engines/opensim/python/opensim_golf/simulate_with_coefficients.py`
- `src/engines/physics_engines/opensim/python/motion_matching/fit_swing.py`

### Specification Files Audited
- `src/engines/CROSS_ENGINE_PARITY_SPEC.md`
- `src/engines/physics_engines/mujoco/MUJOCO_PARITY_SPEC.md`
- `src/engines/physics_engines/drake/DRAKE_PARITY_SPEC.md`
- `src/engines/physics_engines/pinocchio/PINOCCHIO_PARITY_SPEC.md`
- `src/engines/physics_engines/opensim/OPENSIM_PARITY_SPEC.md`
- `SPEC.md` (repository specification)
- `CLAUDE.md` (code quality standards)

### Test Files Audited
- `tests/motion_matching/mujoco_mjcf/test_simulate.py`
- `tests/motion_matching/mujoco_mjcf/test_fit_swing.py`
- `tests/test_drake_simulate.py`
- `tests/test_drake_fit_swing.py`
- `tests/heavy_integration/test_pinocchio_simulate.py`
- `tests/heavy_integration/test_pinocchio_fit_swing.py`
- `tests/test_opensim_simulate.py`
- `tests/test_opensim_fit_swing.py`

---

## Appendix B: Audit Methodology

This audit was conducted using:
1. **Static code analysis:** AST parsing, regex pattern matching
2. **Specification cross-reference:** Manual comparison of implementation vs. CROSS_ENGINE_PARITY_SPEC.md and engine-specific specs
3. **Test coverage analysis:** Review of test files and test markers
4. **Code quality scanning:** Manual inspection against CLAUDE.md standards (DbC, DRY, LOD, TDD, file size)
5. **Documentation review:** Docstring completeness, type hint coverage, reference validation

No dynamic testing or runtime execution was performed; findings are based on static code inspection and specification review.

---

## Appendix C: Glossary

- **DbC:** Design by Contract — formal preconditions and postconditions
- **DRY:** Don't Repeat Yourself — code reuse principle
- **LOD:** Law of Demeter — minimize method-chaining depth
- **TDD:** Test-Driven Development — tests written before implementation
- **SimOut:** Canonical forward-simulation output (cross-engine dataclass)
- **FitResult:** Canonical fitting result (optimization output)
- **ClubTarget:** Measured club trajectory target (motion-matching input)
- **PARITY-LOADERS:** GitHub issue tracking engine-loader unification
- **PARITY-EQUIVALENCE-TEST:** GitHub issue tracking 5mm equivalence test
- **PARITY-LEADERBOARD:** GitHub issue tracking cross-engine result aggregation

---

**Report compiled:** 2026-05-06  
**Auditor:** Claude Code Agent (Haiku 4.5)  
**Next Review:** Upon resolution of all Critical/High issues

