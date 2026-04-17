# [HIGH] Repo-wide code-quality antipatterns: `if not (x is not None)` (×325), prints in src/, precondition-decorator abuse

## Summary

A repository-wide pattern of `if not (x is not None): raise ValueError("x must be provided")`
appears in 50+ files and totals **325 occurrences**. This is an
unreadable double-negative for a trivial None check; it is also
evidence of mass-automated code generation or rewriting. Several
other repo-wide defects compound the signal-to-noise problem.

## Findings

### 1. `if not (x is not None)` pattern — 325 occurrences in 50+ files

Representative examples:
- `src/api/local_server.py:214` — `if not (tile_id is not None):`
- `src/api/auth/security.py:103` — `if not (secret_key is not None):`
- `src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:328`
- `src/robotics/core/types.py`, `src/research/mpc/controller.py`, `src/learning/rl/base_env.py`, and ~45 more.

Full list obtained via `Grep` shows **325 total occurrences**.

The idiomatic Python is `if x is None:`. The pattern hurts reading
comprehension, violates LOD (CLAUDE.md § "Coding Standards"), and is
a tell of auto-generated code. It should be removed in a single
mechanical refactor.

### 2. Redundant precondition decorators + explicit `if not (x is not None)` checks

Several files apply `@precondition(...)` and then repeat the same
check with `if not (x is not None): raise ValueError`. Pick one
style (the decorator is preferable for docstring discoverability).

### 3. Prints inside `src/` — 87 occurrences in 46 files

CLAUDE.md § 46 says no `print()` in `src/`. `Grep -c "print\s*\("
src --glob "*.py"` returns 87 hits across 46 files (many are inside
guarded `if __name__ == "__main__"` sections, but not all). Every
remaining print in library code must be replaced with structured
logging.

The following modules are notable:
- `src/shared/python/physics/aerodynamics.py` (1 print)
- `src/shared/python/physics/physics_validation.py` (1)
- `src/shared/python/spatial_algebra/manipulability.py` (5)
- `src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/drift_control.py` (2)
- `src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/screw_kinematics.py` (4)
- …

### 4. Bare `except Exception: pass` in production paths

`src/shared/python/perturbation/analyzer_base.py:125` logs at DEBUG
and continues; for Monte Carlo batches this silently eats all
failed trials. Also in `.gaai/` and `.github/workflows/` shell
scripts (those are helper scripts — but should still fail loudly).

### 5. Module-level `sys.modules[...] = MagicMock()` in 5 test files

Covered in issue #027; listed here because it is a code-quality
antipattern that CLAUDE.md explicitly forbids.

### 6. `raise NotImplementedError` returned from production code path

- `src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:312` (contact forces; see issue #013)
- `src/launchers/cross_engine_dashboard.py:624`

Should instead report missing capability via `capabilities.py` and
fail at engine-selection time.

### 7. 1-off maintenance scripts in repo root

`count_prints.py`, `count_prints_ast.py`, `patch_analyzers.py`,
`replace_prints.py` sit at the repo root. They should be in `scripts/`
or removed entirely.

### 8. Duplicate boilerplate inside engine directories

Each engine subdirectory (drake, mujoco, pinocchio, pendulum_models,
etc.) ships a `LICENSE`, `JULES_ARCHITECTURE.md`, `Modification_Guidance.md`,
and sometimes a `mypy.ini` / `ruff.toml`. These duplicate or drift
against the repo-root equivalents; overrides are silent.

### 9. Committed generated artifacts

- `coverage.json` (9.9 MB)
- `bandit_results.json` (436 KB)
- `matlab_quality_report.txt` (0 bytes, stale)
- `test.npz` (2.3 KB)
- `temp_id.txt` (12 bytes)

None of these belong in the tree. Add to `.gitignore` and remove in
a single history-preserving commit (squash acceptable).

### 10. 56 GitHub workflows — 31 under the `Jules-*` umbrella

`.github/workflows/` has **56** workflow files (31 `Jules-*`
orchestrator workflows). `ci-standard.yml` itself documents the
overlap in a header comment. Consolidate or at minimum document
which workflows are canonical vs. experimental.

### 11. Multiple agent-framework directories at the root

`.gaai/`, `.jules/`, `.Jules/`, `.kiro/`, `.agent/`, `.claude/` —
six top-level directories for (possibly abandoned) agent frameworks.
Document which are active; delete or archive the rest.

### 12. Formatter drift between `CLAUDE.md`, `CONTRIBUTING.md`, `Makefile`, and pre-commit

- CLAUDE.md § 33: Ruff (NOT Black)
- CONTRIBUTING.md line 40: "Formatter: Black"
- `Makefile` line 48: `black .`
- `pyproject.toml`: Ruff only
- `.pre-commit-config.yaml`: Ruff only

Four sources of truth, two disagree with each other, one with CI.

## Impact

A new contributor cannot easily tell what the repo's coding standard
is, what is canonical, or what is abandoned. The double-negative
pattern alone is 325 lines of technical debt that can be fixed in
a single PR.

## Acceptance Criteria

- [ ] Mechanical refactor: replace `if not (x is not None): raise
      ValueError("x must be provided")` with the idiomatic
      `if x is None: raise ValueError("x must not be None")` across
      the entire repo in one PR. Add a pre-commit regex hook to
      prevent reintroduction.
- [ ] Eliminate remaining `print()` in `src/`; replace with
      `logger.info/debug/warning`.
- [ ] Replace `except Exception: pass` with narrower excepts;
      `analyzer_base.py` should at minimum count and log failures
      with a threshold beyond which it raises.
- [ ] Remove module-level `sys.modules[...] = MagicMock()` (also
      covered by issue #027).
- [ ] Remove `raise NotImplementedError` from production code paths;
      report capability via `capabilities.py`.
- [ ] Move root-level maintenance scripts into `scripts/`.
- [ ] De-duplicate engine-subdirectory boilerplate (LICENSE,
      mypy.ini, ruff.toml); single root source of truth.
- [ ] Add the committed artifacts to `.gitignore` and remove.
- [ ] Consolidate `.github/workflows/` to a documented canonical set;
      move the rest into `.github/workflows/experimental/` or delete.
- [ ] Document `.gaai/`, `.jules/`, `.claude/`, `.kiro/`, `.agent/`
      status in a top-level `.agents.README`.
- [ ] Normalize formatter references: CONTRIBUTING.md, Makefile,
      and `.pre-commit-config.yaml` all must say "Ruff". Remove Black
      from the Makefile.

## Related

- Issue #027 — test mocks.
- Issue #032 — CI / docs / hygiene deep dive.
- Issue #033 — build / deploy hardening.
