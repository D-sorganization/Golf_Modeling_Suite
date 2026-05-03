# Headless Windows CI Remediation Report

The headless CI pipeline for `UpstreamDrift` was failing due to 0xc0000139 fatal DLL exceptions on Windows, which was tracked down to eager imports of `PyQt6` and other GUI libraries during pytest collection. After deploying a codebase-wide skip-guard script (`patch_gui_tests.py`), the DLL crashes were completely resolved. However, this exposed significant underlying test collection errors.

## Finalizing Pytest Collection Stability

The following steps were taken to eliminate all `ModuleNotFoundError` and `SyntaxError` regressions, resulting in a perfectly clean `pytest --collect-only` run:

### 1. Vendor Path Resolution
**Issue:** `pytest` could not resolve imports from `vendor/ud-tools/src` when references like `src.shared.python.calc_backend` were evaluated.
**Fix:** Modified `tests/conftest.py` to correctly identify and inject `vendor/ud-tools` into `sys.path` dynamically.

### 2. Orphaned "Mission Drift" Tests Cleanup
**Issue:** Commit `367e87c62` ("execute C4 mission-drift audit") successfully stripped legacy `calc_backend` and `process_calculators` modules from the UpstreamDrift codebase and moved them to the vendored `ud-tools` module. However, 71 tests belonging to these deleted components were left orphaned in the `tests/unit/calc_backend` and `tests/unit/process_calculators` directories. Because they pointed to deleted files, they caused `ModuleNotFoundError` exceptions.
**Fix:** Removed 71 orphaned test files using a targeted automated script. The components are now properly tested directly inside `vendor/ud-tools/tests/`.

### 3. Syntax Error Remediation (`from __future__ import annotations`)
**Issue:** The automated skip-guard insertion occasionally placed code before `from __future__ import annotations` (if the future import followed a docstring), resulting in Python `SyntaxError: from __future__ imports must occur at the beginning of the file`.
**Fix:** Executed an automated pass across 586 test files, migrating all `from __future__ import annotations` statements to the absolute top line.

### 4. Resolving Duplicate Module Names (`test_rate_limiting.py`)
**Issue:** `pytest` rejected collection due to a module name collision between `tests/api/test_rate_limiting.py` (which thoroughly tests the `/simulate` endpoint) and `tests/security/test_rate_limiting.py` (which contained a stubbed, xfail test for a non-existent auth endpoint).
**Fix:** Renamed `tests/security/test_rate_limiting.py` to `test_auth_rate_limiting.py`.

### 5. Suppressing Sys.Modules Pollution (`test_panel_builders_helpers.py`)
**Issue:** `test_panel_builders_helpers.py` had a manual headless skip guard implemented *after* it monkey-patched `sys.modules` to mock engine controllers. Because it skipped mid-execution, it never reached its `finally` block to restore `sys.modules`, thereby crashing subsequent tests (e.g., `test_perturbation_analysis.py`).
**Fix:** Moved the skip guard above the mocking logic to ensure `sys.modules` remains clean when skipped. Added `allow_module_level=True` to its `pytest.skip` call.

## Result
Executing `python -m pytest tests/ -q --collect-only` now successfully processes the entire test suite, registering 0 errors.

All GUI imports are safely guarded, and the `fix/pytest-headless-collection-3910` PR is ready to merge.
