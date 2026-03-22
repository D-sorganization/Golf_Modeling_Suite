# Assessment C Results: Documentation & Integration

## Executive Summary

- The repository boasts extensive architectural `README.md` coverage at the component level, with 70+ READMEs identified across `src/` and `docs/`.
- Function-level docstring coverage is statistically excellent (`~19,000` docstring lines vs `~12,000` function definitions), but qualitative audits reveal many docstrings are out of sync with actual parameter lists or function capabilities (e.g., documenting full features where only stubs exist).
- The "Integration Experience" relies heavily on undocumented assumptions about environmental states (e.g., Docker container constraints, specific conda environments for `opensim`, unauthenticated pull rate limits on Docker Hub).
- Examples provided in `src/shared/python/optimization/examples` and `src/engines/` often lack explicit execution instructions or rely on deprecated CLI arguments.
- `AGENTS.md` and `README.md` in the root repository serve as a strong entry point, but deeply nested MATLAB and Unreal Engine components lack corresponding "Getting Started" pathways for developers outside those niches.

## Top 10 Documentation Gaps

1. **Critical:** Missing documentation for hardware/controller connectivity workflows. The reliance on `NotImplementedError` is not documented as the expected state for users expecting a plug-and-play experience.
2. **Critical:** No central documentation detailing the patent-risk mitigation strategies currently active in the codebase (e.g., why haptic feedback is clipped, or why DTW is restricted).
3. **Major:** Docstrings for `flexible_shaft.py` and `flight_models.py` describe fully realized physical models but the actual code is largely stubbed.
4. **Major:** Outdated setup instructions regarding `opensim`; users will hit pip errors unless they manually read the implicit memory/issue trackers.
5. **Major:** Docker limitations (overlayfs, rate limits) are not prominently documented in the `README.md` installation section.
6. **Major:** Missing API documentation for the `GMS-XXX-NNN` error code schema.
7. **Minor:** Fragmented `README.md` files in `src/engines/Simscape_Multibody_Models/` that point to local network paths rather than relative repository paths.
8. **Minor:** Missing "Why" comments in complex MuJoCo XML generation scripts.
9. **Minor:** Examples in `docs/tutorials/` are decoupled from CI, meaning they are prone to bit-rot.
10. **Minor:** Trademark risks ("Kinematic Sequence") are still present in GUI strings, meaning the UI documentation is out of compliance with the master risk register.

## Scorecard

| Category | Description | Weight | Score | Evidence / Remediation |
| :--- | :--- | :--- | :--- | :--- |
| README Quality | Clear, complete, actionable | 2x | 8 | **Evidence:** Broad coverage, but environmental assumptions omitted. **Remediation:** Add explicit Docker constraint section. |
| Docstring Coverage | All public functions documented | 2x | 7 | **Evidence:** High volume, low accuracy (stub masking). **Remediation:** Audit docstrings against actual implementations. |
| Example Completeness | Runnable examples provided | 1.5x | 5 | **Evidence:** Examples frequently fail due to missing dependencies (`opensim`). **Remediation:** Add `pytest.mark.skipif` logic to examples or formalize requirements. |
| Tool READMEs | Each tool has documentation | 2x | 9 | **Evidence:** Almost all discrete tools have a local README. |
| Integration Docs | How tools work together | 1x | 4 | **Evidence:** Multi-engine integration (MuJoCo + Unreal) is tribal knowledge. **Remediation:** Write an E2E pipeline tutorial. |
| API Documentation | Programmatic usage guides | 1x | 5 | **Evidence:** Missing error schema docs; auth APIs stubbed. |
| Onboarding Experience | Time-to-productivity | 1.5x | 6 | **Evidence:** Launchers help, but pip install failures block quick onboarding. |

## Documentation Inventory

| Category | README | Docstrings | Examples | API Docs | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/shared/physics` | ✅ | ~90% (Inaccurate) | N/A | ❌ | Partial |
| `src/launchers` | ✅ | ~70% | ✅ | ❌ | Complete |
| `src/api` | ✅ | ~80% | N/A | ✅ | Partial |
| `src/engines/mujoco` | ✅ | ~60% | ✅ | ❌ | Partial |
| `src/deployment/realtime` | ❌ | ~40% | N/A | ❌ | Missing |

## User Journey Analysis

**Journey 1: "I want to run a physics simulation"**
1. Start point: Repository root
2. Expected path: README → `src/engines/physics_engines/mujoco/README.md` → Launch script
3. Actual experience: Fails if optional dependencies (e.g. strict `matplotlib` bounds) are met, or hits stubbed physics calculations.
4. Grade: C

**Journey 2: "I want to integrate a new launcher tool"**
1. Start point: `src/launchers/README.md`
2. Expected path: Guidelines → Add to Registry → Execute
3. Actual experience: Confusing fragmentation between `unified_launcher`, `golf_suite_launcher`, and `mujoco_unified_launcher`.
4. Grade: D

## Refactoring Plan

**48 Hours**
- Update root `README.md` with explicit warnings about Docker Hub rate limits and the `opensim` pip installation issue.
- Add documentation for the `GMS-XXX-NNN` error code schema.

**2 Weeks**
- Audit and rewrite docstrings in `src/shared/python/physics/` to accurately reflect the stubbed nature of the code (preventing false expectations).
- Consolidate launcher documentation into a single definitive guide.

**6 Weeks**
- Establish a CI workflow that executes `docs/tutorials/` examples to prevent bit-rot.
- Publish a comprehensive "Hardware Integration Guide" explicitly defining the `NotImplementedError` state machine.

## Diff Suggestions

**Suggestion 1: Update README for opensim**
```markdown
<<<<<<< SEARCH
## Installation
1. `pip install -r requirements.txt`
=======
## Installation
1. `pip install -r requirements.txt`
   *(Note: The `opensim` package is currently commented out due to Docker build constraints. It must be installed manually via conda if required.)*
>>>>>>> REPLACE
```

**Suggestion 2: Accurate Docstrings for Stubs**
```python
<<<<<<< SEARCH
def simulate_flexible_shaft(load: float) -> np.ndarray:
    """
    Simulates the non-linear bending and torsional dynamics of a golf shaft under load.
    Returns a 6-DOF deformation vector.
    """
    pass
=======
def simulate_flexible_shaft(load: float) -> np.ndarray:
    """
    Simulates the non-linear bending and torsional dynamics of a golf shaft under load.
    Returns a 6-DOF deformation vector.

    WARNING: Currently implemented as a stub. See Issue #2083.
    """
    pass
>>>>>>> REPLACE
```
