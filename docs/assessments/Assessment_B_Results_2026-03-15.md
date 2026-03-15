# Assessment B Results: Hygiene, Security & Quality

## Executive Summary
* Baseline hygiene is enforced via Ruff and Mypy but major gaps exist.
* 454 pre-existing Ruff T201 (print) violations present.
* Critical security flaw in `SECRET_KEY` fallback.
* Hash collision risk in AuthCache.
* Several missing docstrings and bare except clauses.

## Top 10 Hygiene Risks
1. [CRITICAL] `SECRET_KEY` fallback to known public string.
2. [CRITICAL] AuthCache uses `hash()` instead of HMAC-SHA256.
3. [MAJOR] 454 print statements in production code.
4. [MAJOR] Bare `pass` in `except` blocks in API routes.
5. [MAJOR] Missing `@precondition` on `compute_acceleration`.
6. [MAJOR] Token expiry is 30 days (too long).
7. [MINOR] `TopographyData._load_csv` silently handles missing columns.
8. [MINOR] `auth_cache` is a module-level global.
9. [MINOR] Missing `__init__.py` in some plugin dirs.
10. [MINOR] 13 redundant disabled CI workflows.

## Scorecard
| Category | Score | Weight | Evidence |
|---|---|---|---|
| Ruff Compliance | 6/10 | 2x | 454 T201 violations |
| Mypy Compliance | 8/10 | 2x | Good coverage, some `# type: ignore` |
| Black Formatting | 9/10 | 1x | Formatted mostly |
| AGENTS.md Compliance | 5/10 | 2x | Prints used, bare excepts |
| Security Posture | 4/10 | 2x | `SECRET_KEY` fallback is unsafe |
| Repository Organization | 7/10 | 1x | Clean but some orphaned files |
| Dependency Hygiene | 8/10 | 1x | Pinned correctly |

## Linting Violation Inventory
| File | Ruff Violations | Mypy Errors | Black Issues |
|---|---|---|---|
| `kinematic_forces.py` | T201 (18) | 0 | None |
| `sim_widget.py` | E722 (2) | 0 | None |
| `security.py` | S104 (1) | 0 | None |

## Security Audit
| Check | Status | Evidence |
|---|---|---|
| No hardcoded secrets | ❌ | `SECRET_KEY = "UNSAFE..."` |
| .env.example exists | ✅ | File present |
| No eval()/exec() usage | ✅ | Clean |
| No pickle without validation | ✅ | Clean |
| Safe file I/O | ❌ | `TopographyData` lacks path validation |

## AGENTS.md Compliance Report
1. No `print()`: Failed (454 violations).
2. No wildcard imports: Passed.
3. No bare `except:`: Failed (`sim_widget.py`, etc.).
4. Type hints required: Mostly Passed.
5. No secrets in code: Failed (`SECRET_KEY`).

## Findings Table
| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
|---|---|---|---|---|---|---|---|
| B-001 | CRITICAL | Security | `security.py:43` | Predictable key | Fallback string | Raise RuntimeError | S |
| B-002 | CRITICAL | Security | `security.py:210` | Hash collision | `hash()` | Use HMAC | S |
| B-003 | MAJOR | Hygiene | `kinematic_forces.py` | Console spam | `print()` | Use `logging` | S |

## Refactoring Plan
**48 Hours**: Fix `SECRET_KEY` fallback to raise an exception.
**2 Weeks**: Replace all `print()` with `logger.info()`.
**6 Weeks**: Enforce strict ruff compliance in CI.

## Diff Suggestions
```python
<<<<<<< SEARCH
SECRET_KEY = os.environ.get("SECRET_KEY", "UNSAFE-NO-SECRET-KEY-SET-AUTHENTICATION-WILL-FAIL")
=======
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is missing.")
>>>>>>> REPLACE
```

## Appendix: Files Requiring Attention
- `src/api/auth/security.py`
- `src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/advanced_gui_methods.py`
