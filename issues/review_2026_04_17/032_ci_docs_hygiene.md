# [MEDIUM] CI / docs / hygiene: 56 workflows, formatter drift, committed artifacts, duplicate LICENSE

## Summary

Cross-cutting concerns that impact developer velocity and
repo maintainability. None of these are physics-critical, but in
aggregate they obscure the signal and make every other fix harder.

## Findings

### 1. Formatter drift between Makefile, CONTRIBUTING.md, and pre-commit

- `Makefile` lines 48–53 run `black .` then `ruff format .`.
- `CONTRIBUTING.md` lines 40, 64 say Black is the formatter.
- `CLAUDE.md` § 33 says Ruff (NOT Black).
- `.pre-commit-config.yaml` runs Ruff only.
- Black is not in `pyproject.toml` dev dependencies.

Pick Ruff; remove every reference to Black.

### 2. Committed artifacts

- `coverage.json` (9.9 MB)
- `bandit_results.json` (436 KB)
- `matlab_quality_report.txt` (0 bytes)
- `test.npz` (2.3 KB)
- `temp_id.txt` (12 bytes)

Add to `.gitignore`, remove from the tree. Consider `git filter-repo`
if repo size matters.

### 3. 56 GitHub workflows, 31 under `Jules-*`

`.github/workflows/ci-standard.yml` itself documents known overlaps:

> Jules-Assessment-Remediator.yml ↔ auto-remediate-issues.yml
> assessment-auto-fix.yml ↔ Jules-Assessment-AutoFix.yml
> Jules-Code-Quality-Fixer ↔ Jules-Assessment-AutoFix

Plus there is a Jules-PR-AutoFix, Jules-Auto-Repair, Jules-Hotfix-Creator,
Jules-Comment-Processor, Jules-Conflict-Fix, etc. — many of these likely
conflict with each other when auto-committing to the same branch.

**Action:** audit, consolidate, and move experimental workflows to
`.github/workflows/experimental/`.

### 4. CI matrix is Ubuntu-only

`ci-standard.yml` runs on `ubuntu-latest` for Python 3.10/3.11/3.12.
No Windows, no macOS. The repo ships Windows-only launcher scripts
(`.bat`, `.ps1`) that have no Linux equivalents — no CI tests them.

### 5. Agent framework directories at root, status unclear

`.gaai/`, `.jules/`, `.Jules/`, `.kiro/`, `.agent/`, `.claude/` — six
such directories. Only `.gaai/` is documented in `CLAUDE.md`. The
others may be live, archived, or competing.

### 6. Duplicate LICENSE files

Each engine subdirectory (Drake, MuJoCo, Pinocchio, pendulum_models,
Simscape_Multibody_Models/2D, Simscape_Multibody_Models/3D) has its
own `LICENSE` file. Aside from third-party vendored code (e.g.
`src/shared/models/myosuite/myo_sim/LICENSE` which is legitimately
third-party), these duplicate the root LICENSE.

### 7. Duplicate per-engine `mypy.ini` and `ruff.toml`

Drake, MuJoCo, Pinocchio each have their own config overriding the
root. Strictness diverges: Drake has `disallow_any_unimported = True`,
MuJoCo has `False`. Code written to pass one engine fails the other.

### 8. Nested `pyproject.toml` in Pinocchio engine subdirectory

`src/engines/physics_engines/pinocchio/pyproject.toml` is not
referenced by the root build but exists as a sub-package config.
Document whether the engine is installable independently or remove.

### 9. SPEC.md is 654 lines but has no update enforcement

CLAUDE.md says "Update [SPEC.md] when your changes affect documented
functionality, features, or architecture." No CI gate, no
changelog requirement, no PR template field.

### 10. CONTRIBUTING.md contradicts CLAUDE.md on formatter (see #1)

### 11. Lock files are committed but rapidly stale

`requirements.lock` and `requirements-dev.lock` are committed and
will merge-conflict on every dependency update. Either freeze them
per-release or move to `pip-compile` on CI only.

### 12. Pre-push pytest hook limited to a sliver of the suite

`.pre-commit-config.yaml` runs only `tests/unit/dbc`, `tests/unit/core`,
`tests/unit/utils` on pre-push because of unresolved state pollution.
That pollution should be fixed (it is the `sys.modules` mocking from
issue #027) so pre-push can run the real unit suite.

### 13. `bandit_results.json` exists but there is no workflow to refresh it

Committing a one-off scan result creates false confidence. Either
run bandit in CI and upload as an artifact, or remove.

### 14. No Dependabot security audit in CI output

`.github/dependabot.yml` exists but is not inspected in detail; pair
it with an automatic `pip-audit` step in `ci-standard.yml`.

### 15. `AGENTS.md` (643 lines) and `CLAUDE.md` (CLAUDE.md 62 lines)
     and the agent directories — documentation overlap

`AGENTS.md` and `CLAUDE.md` partially cover the same conventions.
Deduplicate; make one of them the canonical engineering-standards
document and reduce the other to a stub with a link.

### 16. `docs/` has nested `assessments/`, `audit_reports/`, `historical/`
     dating unclear

Some documentation sub-trees (e.g. `docs/historical/`) may be stale;
no freshness badges.

### 17. `bandit` ignores & `# nosec` usage is not audited

`src/shared/python/data_io/io_utils.py:210` has `# nosec B506` —
justified, but there is no audit pass that enumerates all nosec
suppressions.

## Impact

These do not change the physics, but they raise the cognitive cost of
every downstream PR, confuse new contributors, inflate the repo, and
hide real problems behind noise.

## Acceptance Criteria

- [ ] Remove all references to Black; Ruff is the sole formatter.
- [ ] `.gitignore` committed artifacts; remove from tree.
- [ ] Audit `.github/workflows/`: document canonical set, move or
      delete the rest.
- [ ] Extend CI matrix to macOS and Windows (at least for unit tests).
- [ ] Document agent-framework directory status in
      `.agents.README.md`.
- [ ] Consolidate LICENSE files; keep only (a) root and (b)
      third-party-vendored.
- [ ] Unify per-engine `mypy.ini` / `ruff.toml` with the root config;
      document any justified exceptions.
- [ ] Document or remove the nested Pinocchio `pyproject.toml`.
- [ ] Add SPEC.md freshness check: PR-template item + CI lint on last-
      modified date vs. source-code change paths.
- [ ] Deduplicate `AGENTS.md` ↔ `CLAUDE.md` ↔ CONTRIBUTING.md on
      formatter/linter guidance.
- [ ] Move lock-file generation to CI; remove from tree *or* pin per
      release tag.
- [ ] Fix `sys.modules` pollution (issue #027) and restore full
      pre-push pytest.
- [ ] Generate `bandit_results.json` in CI as an artifact; remove
      committed copy.
- [ ] Enable `pip-audit` step in `ci-standard.yml`.
- [ ] Audit `# nosec` / `# noqa` suppressions; document each.

## Related

- Issue #031 — repo-wide antipatterns.
- Issue #033 — build / Docker hardening.
