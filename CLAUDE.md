# CLAUDE.md — UpstreamDrift

> **GAAI Fleet Member.** GAAI framework installed in `.gaai/`. Read `.gaai/core/GAAI.md` for full governance spec.
> Rules: `@.gaai/core/contexts/rules/base.rules.md` and `@.gaai/project/contexts/rules/project.rules.md`
> All work on `staging` branch. PRs target `staging`. Never push directly to `main`.

## What This Is

Golf ball flight and physics modeling suite. Simulates aerodynamics, ball-club impact,
and trajectory using multiple physics engines (MuJoCo, Drake, Pinocchio, OpenSim).
Optional Rust extensions built via Maturin for performance-critical paths.

## Key Directories

- `src/` — core library: physics wrappers, URDF loaders, simulation runners
- `tests/` — pytest suite (unit, integration, live simulation)
- `scripts/` — CI helpers including `check_file_size_budget.py`
- `scripts/config/file_size_budget.json` — per-file size exceptions
- `module_size_budget_baseline.json` — modules exceeding default size limits
- `rust/` — optional Rust features built with Maturin

## Python and Tooling

- **Python 3.10+**. Always `python3`, never `python`.
- **Formatter:** Ruff format (NOT Black). 88-char line limit.
- **Linter:** Ruff check. These are **separate CI steps** — both must pass independently.

## Development Commands

```bash
python3 -m ruff check .                          # lint
python3 -m ruff format --check .                  # format check
python3 -m ruff format .                          # auto-format
python3 -m pytest -n auto --timeout=60            # full test suite
python3 -m pytest -m unit -n auto --timeout=60    # unit tests only
python3 -m pytest -m "not slow and not live_simulation" -n auto --timeout=60
python3 scripts/check_file_size_budget.py         # file size check
maturin develop                                   # build Rust extensions locally
```

## CI Requirements (All Must Pass)

1. `ruff check` — zero violations
2. `ruff format --check` — zero diffs (separate step from lint)
3. File size budget: **1200 lines max** per file. Exceptions in `scripts/config/file_size_budget.json`
4. Module size budget: checked against `module_size_budget_baseline.json`
5. No TRACKED_TASK/TRACKED_DEFECT unless tied to a tracked GitHub issue
6. pytest with `-n auto`, 60s timeout, **10% coverage minimum**
7. No `print()` in `src/` — use logging

## Test Markers

`unit`, `integration`, `slow`, `live_simulation`, `requires_gl`, `headless_safe`,
`benchmark`, `scientific`

## Physics Engine Gotchas

- **Pinocchio:** NO `computeTotalEnergy`. Use `computeKineticEnergy` + `computePotentialEnergy` separately.
- **Drake:** Must use explicit imports: `from pydrake.X import Y`. Attribute access on `pydrake` namespace does not work. Use `body.body_frame()` directly, NOT `FixedOffsetFrame`.
- **Test pollution:** Never `sys.modules["pydrake"] = MagicMock()` at module level. Use `patch.dict("sys.modules", ...)` which auto-cleans after the test.

## Known Constraints

- **Branch naming:** `fix/issue-XXXX-description`
- **Remote:** origin URL references `Golf_Modeling_Suite.git`
- Rust builds: `maturin develop` for local dev; CI handles wheel builds

## CI Fixes (2026-04-18)

### Ruff pip Conflict Fix

**Issue:** CI workflow failed with `Cannot uninstall ruff None - The package's contents are unknown: no RECORD file was found for ruff`

**Root Cause:** Version mismatch between ruff specifications:

- `.pre-commit-config.yaml` pinned to v0.14.10
- CI quality-gate job directly installed ruff==0.14.10
- `pyproject.toml` dev dependencies required ruff>=0.15.10
- When `pip install -e .[dev]` ran, it tried to upgrade ruff, causing metadata corruption on cached runners

**Fix Applied:**

1. Synchronized `pyproject.toml` dev dependencies to `ruff==0.14.10` (matching pre-commit)
2. Updated CI quality-gate job to create a fresh venv before installing dependencies
3. Added `--force-reinstall --no-cache-dir` flags to ensure clean package metadata
4. Pre-installed ruff and other tools in the venv before `pip install -e .[dev]`

**Files Modified:**

- `pyproject.toml`: Changed `ruff>=0.15.10` to `ruff==0.14.10` (line 69)
- `.github/workflows/ci-standard.yml`: Added venv creation step in quality-gate job (lines 92-103)

## Coding Standards (Enforced by CI and QA)

- **DRY:** No duplicated logic blocks >5 lines. CI tracks DRY adoption metrics.
- **DbC:** Public functions validate preconditions, raise `ValueError`/`TypeError` with descriptive messages. Document postconditions in docstrings.
- **LOD:** No method chains >2 levels (`a.b.c.d()` violates). Add delegating methods instead.
- **TDD:** Tests in same PR as implementation. Coverage must not decrease.
- **File size:** If approaching 1200 lines, refactor before adding more.

## Cross-Repo Dependencies

- **Imports from Tools** (D-sorganization/Tools): URDF generation, signal processing, shared utilities.
- Breaking changes to Tools public API require a coordinated PR here.
- Gasification_Model also depends on Tools — avoid transitive breakage.

## Slash Commands

- `/gaai-deliver` — Run Delivery Loop for next ready backlog item
- `/gaai-status` — Show current backlog and memory state

## Stale PR & GAAI Framework Handling

### Why GAAI Framework Conflicts Occur

The GAAI framework was introduced in commit `3b30062d6` ("feat: install GAAI framework v2.6.3 for fleet-driven autonomous delivery"). Branches created **before** this commit do not have the `.gaai/` directory structure, which causes merge conflicts when trying to merge them into `staging` or `main`. The framework includes:

- `.gaai/core/` — immutable framework rules, scripts, and contexts (rarely modified)
- `.gaai/project/contexts/rules/` — project-specific rule overrides
- `.gaai/project/contexts/backlog/` — automated backlog and delivery state

Stale branches attempting to merge after the framework introduction conflict on framework files that didn't exist in their history.

### Three-Tiered Resolution Strategy

#### Tier 1: Framework-Only Branches (Recommended for Minor Changes)

**Use when:** The branch contains only framework/config changes, no significant feature work.

**Steps:**

```bash
# Rebase the stale branch onto the commit BEFORE framework installation
git rebase --onto 3b30062d6^ <branch-base> <branch-name>

# Example: For a branch "fix/issue-1234" based on main from before the framework
git checkout fix/issue-1234
git rebase --onto 3b30062d6^ main fix/issue-1234

# Then merge into staging (framework will already be present)
git checkout staging
git merge fix/issue-1234
```

**Result:** The branch's commits are replayed on top of the pre-framework state, then you merge into `staging` which already has the framework.

#### Tier 2: Content-Preserving Merges (For Significant Feature Branches)

**Use when:** The branch has substantial feature work and the conflicts are manageable.

**Steps:**

```bash
# Attempt merge with conflict markers
git checkout staging
git merge --no-ff <branch-name>

# Resolve conflicts manually:
# - For .gaai/core/** and .gaai/project/contexts/backlog/**: Accept staging version
# - For project code conflicts: Manually resolve using domain knowledge
# - For project rule overrides: Merge both versions if they address different rules

git add .
git commit -m "merge: resolve GAAI framework conflicts (content-preserving)"
```

**Prevention:** Use `.gitattributes` merge drivers (see below) to auto-resolve framework files.

#### Tier 3: Hard Reset Approach (For Low-Priority or Abandoned Branches)

**Use when:** The branch is low priority or its changes can be cherry-picked onto a fresh branch.

**Steps:**

```bash
# Create a new branch from staging with the same base name
git checkout staging
git pull origin staging
git checkout -b <branch-name>-v2

# Cherry-pick only the significant commits from the stale branch
git cherry-pick <commit-hash-1>
git cherry-pick <commit-hash-2>
# ... resolve any conflicts during cherry-pick

# Merge the new branch
git merge --ff-only <branch-name>-v2
```

**Result:** Clean history, but original branch history is discarded.

### Prevention: Merge Driver Configuration

Add the following to `.gitattributes` to automatically resolve framework conflicts:

```
.gaai/core/** merge=theirs
.gaai/project/contexts/backlog/** merge=theirs
```

This tells Git to **always accept the current branch's (staging) version** of framework files during merges, preventing manual conflict resolution for these files.

Configure the merge driver in `.git/config`:

```bash
git config merge.theirs.driver 'git checkout --theirs %P'
git config merge.theirs.name 'accept their version'
```

### Pre-Push Verification Hook

Before pushing to `staging` or `main`, verify that `.gaai/` files are consistent:

```bash
# Check that framework files match main/staging
git diff main .gaai/core/ --quiet || {
  echo "WARNING: .gaai/core/ differs from main"
  echo "If this is unintended, resolve conflicts before pushing"
  exit 1
}
```

### When Framework Itself Needs Updates

If the GAAI framework requires updates (rules, scripts, backlog structure):

1. **Never merge from external branches.** Update framework files directly on `staging`.
2. **Create a dedicated "framework-update" commit** with all framework changes.
3. **Document the change** in `.gaai/core/CHANGELOG.md` or this CLAUDE.md section.
4. All downstream stale branches should use **Tier 1 or 2** to rebase onto the updated framework.

## Specification

This repository's specification is defined in `SPEC.md` at the repo root.
Read SPEC.md before making any changes. Update it when your changes
affect documented functionality, features, or architecture.
