# Assessment I Results: Code Style & Conventions

## Executive Summary

- Code styling is predominantly driven by a very strict set of rules defined within `pyproject.toml` using `ruff` (enforcing `E`, `F`, `I`, `UP`, `B`, `T201`, `SIM`, `C4`, `PIE`, `PLE`, `FURB`, `RSE`, and `LOG` rules).
- The use of the standard 88-character line length aligns with Black defaults, ensuring uniform multi-developer contributions.
- Third-party models (e.g., `opensim-models`, `myosuite`, `vendor/`) are explicitly excluded from formatting checks. While necessary for legacy Python 2 scripts, this masks potentially unsafe paradigms from SAST tools.
- There are documented deviations from the core style guides: specifically, backslash (`\`) usage inside f-strings and hardcoded string encodings in `open()` calls. These consistently trip `ruff` CI checks (notably `UP015` and `F-string` errors on Python 3.11).
- Mypy configurations enforce strict type checking, though developers circumvent these using `# type: ignore` comments instead of proper variable narrowing, establishing a brittle type-safety culture.

## Top 10 Styling Risks

1. **Major:** Active regression in Python 3.11 compatibilities due to developers using Python 3.12+ f-string syntax (e.g., embedded backslashes).
2. **Major:** Missing `# noqa: E402` on specific module-level imports leading to developers relocating necessary runtime paths (e.g., `sys.path.append()`) beneath standard imports, causing cyclic or unresolved dependencies.
3. **Major:** Widespread and unchecked usage of `# type: ignore` decorators, particularly surrounding `@jit(nopython=True)` and complex GUI inheritance trees.
4. **Minor:** The `LOG` rule is enabled but not consistently adhered to, with developers falling back on `print()` (flagged by `T201`).
5. **Minor:** Python 3.10 to 3.11 modernization updates (`UP` rules) are frequently broken in newly created completist generation scripts.
6. **Minor:** The use of `dict()` constructors over `{}` literals (`C4` rule violation) in legacy integration scripts.
7. **Minor:** Extensive reliance on nested `try...except` blocks rather than standardizing on context managers, violating clean code flow patterns (`SIM`).
8. **Minor:** Lack of docstring style enforcement (e.g., missing `pydocstyle` or Ruff's `D` rule group).
9. **Minor:** `exclude` lists in `pyproject.toml` are redundant (specifying both `src/shared/models/` and `shared/models/`).
10. **Minor:** Absence of automated Prettier configuration for `.yaml`, `.json`, and `.md` formatting, creating noise in git diffs.

## Scorecard

| Category | Description | Weight | Score | Evidence / Remediation |
| :--- | :--- | :--- | :--- | :--- |
| Python Linting | Adheres to PEP 8/Ruff | 2x | 8 | **Evidence:** Ruff enforced strongly in CI. **Remediation:** Eradicate `print()` and bad f-strings. |
| Type Hinting | Mypy coverage & accuracy | 2x | 6 | **Evidence:** `# type: ignore` abused heavily. **Remediation:** Mandate type stubs for missing libraries. |
| Documentation Style | Consistent docstrings | 1x | 5 | **Evidence:** Ruff `D` rules missing. **Remediation:** Adopt Google/NumPy style enforcement. |
| Non-Python Formats | YAML, JSON, Markdown | 1x | 4 | **Evidence:** No formatting gates for configs. **Remediation:** Introduce `prettier` via pre-commit. |

## Refactoring Plan

**48 Hours**
- Scrub the codebase for Python 3.12+ f-string backslash usage to resolve Python 3.11 CI execution errors.
- Resolve all `UP015` violations by forcing `encoding='utf-8'` onto `open()` statements across `src/` and `scripts/`.

**2 Weeks**
- Introduce `pydocstyle` or Ruff `D` rules (e.g., `D101`, `D102`) to begin enforcing basic docstring existence and formatting constraints on public API surfaces.
- Standardize the `pyproject.toml` exclude paths, merging redundant `src/` and non-`src/` directory string listings.

**6 Weeks**
- Systematically remove `# type: ignore` suppressions across Numba `@jit` decorators and Matplotlib calls, implementing correct type stubs.
- Add `.editorconfig` to enforce cross-IDE indentation (tabs vs spaces) for Markdown and YAML files.

## Diff Suggestions

**Suggestion 1: Fix F-String Backslash (Python 3.11 Compat)**
```python
<<<<<<< SEARCH
log.info(f"Loaded paths: {\n.join(paths)}")
=======
formatted_paths = "\n".join(paths)
log.info(f"Loaded paths: {formatted_paths}")
>>>>>>> REPLACE
```
