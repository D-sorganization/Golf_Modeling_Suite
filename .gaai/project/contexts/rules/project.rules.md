# Project Rules — UpstreamDrift (GAAI Fleet)

## Safety

# <<<<<<< HEAD

> > > > > > > origin/staging

1. All AI work on `staging` branch. Never commit directly to `main`.
2. PRs target `staging`. No auto-merge. Human approval required.
3. No destructive git history operations.
4. No secret commits (.env, API keys, credentials).

## Quality Gates (CI) — MANDATORY PRE-PR CHECKLIST

**Before creating a PR, the delivery agent MUST run these commands and fix all issues:**

```bash
# Step 1: Auto-format (fixes most issues automatically)
python3 -m ruff format .

# Step 2: Lint and auto-fix what's possible
python3 -m ruff check --fix .

# Step 3: Verify clean (must exit 0)
python3 -m ruff format --check .
python3 -m ruff check .

# Step 4: Run tests on changed files
python3 -m pytest -x --timeout=60 -q
```

**If any step fails after auto-fix, manually resolve before proceeding. Do NOT create a PR with known lint/format failures.**

5. `ruff check` must pass on ALL modified Python files before PR creation.
6. `ruff format --check` must pass (NOT black — this repo uses ruff format).
7. No new `print()` calls in `src/` (use logging).
8. File size budget: max 1200 lines per file. Exceptions in `scripts/config/file_size_budget.json`.
9. Module size budget baseline in `module_size_budget_baseline.json` for modules exceeding default limits.
   <<<<<<< HEAD
10. # No TRACKED_TASK/TRACKED_DEFECT comments unless a tracked GitHub issue exists.
11. No TODO/FIXME comments unless a tracked GitHub issue exists.
    > > > > > > > origin/staging
12. Use `python3` — never bare `python`.
13. Pre-push hook uses `python3 -m pytest` (fixed in #2037). Run `pre-commit install --hook-type pre-push` after cloning.

## CI Watch (Post-PR)
