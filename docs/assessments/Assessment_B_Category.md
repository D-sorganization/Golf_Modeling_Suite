# Assessment B Results: Hygiene, Security & Quality

## Executive Summary

- Ruff E402 and I001 violations in `docker_manager.py`.
- `ruff` UP015 violations (unnecessary `open` mode 'r').
- `print()` statements forbidden (T201).
- API keys absent (use `.env`).
- Data Copyright risk in `validation_data.py`.

## Top 10 Hygiene Risks

1. Copyright risk in `validation_data.py` (TrackMan averages)
2. `ruff` I001 and E402 in `launchers/`
3. Unnecessary UP015 `open()` modes

## Scorecard

| Category | Score | Evidence |
|---|---|---|
| Ruff Compliance | 7/10 | I001 in `docker_manager.py` |
| Security | 6/10 | `validation_data.py` data copyright risk |
| Dependencies | 8/10 | opensim fails in Docker |

## Linting Violation Inventory

| File | Ruff Violations | Mypy Errors | Black Issues |
|---|---|---|---|
| `src/launchers/docker_manager.py` | I001 (1) | 0 | None |

## Security Audit

| File | Ruff Violations | Mypy Errors | Black Issues |
|---|---|---|---|
| `src/launchers/docker_manager.py` | I001 (1) | 0 | None |

## AGENTS.md Compliance Report

- Ruff E402 and I001 violations in `docker_manager.py`.
- `ruff` UP015 violations (unnecessary `open` mode 'r').
- `print()` statements forbidden (T201).
- API keys absent (use `.env`).
- Data Copyright risk in `validation_data.py`.

## Findings Table

| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
|---|---|---|---|---|---|---|---|
| B-001 | Critical | Data | `validation_data.py` | TrackMan averages | Hardcoded proprietary data | Remove TrackMan data | S |
| B-002 | Major | Linting | `docker_manager.py` | I001 | Stdlib imports not sorted | Run `ruff check --fix` | S |

## Refactoring Plan

**48 Hours**
- Remove TrackMan data.
**2 Weeks**
- Fix all `ruff` I001 and E402 violations.

## Diff Suggestions

```python
<<<<<<< SEARCH
with open('file.txt', 'r') as f:
=======
with open('file.txt', encoding='utf-8') as f:
>>>>>>> REPLACE
```

## Appendix: Files Requiring Attention

1. Copyright risk in `validation_data.py` (TrackMan averages)
2. `ruff` I001 and E402 in `launchers/`
3. Unnecessary UP015 `open()` modes