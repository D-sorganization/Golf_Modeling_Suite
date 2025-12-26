---
name: Fix pytest configuration contradiction
about: Resolve conflict between coverage targets and omit patterns
title: '[BUG] Fix pytest configuration contradiction in pyproject.toml'
labels: ['bug', 'priority: high', 'testing', 'phase-1']
assignees: ''
---

## 🐛 Problem Description

The pytest configuration in `pyproject.toml` has a contradiction that causes CI failures. The coverage targets include `engines`, but the coverage omit patterns exclude all engine code.

## 📍 Location

**File:** `pyproject.toml`

**Lines 172-179 (coverage targets):**
```toml
addopts = [
    "--cov=shared",
    "--cov=engines",      # ⚠️ Trying to cover engines
    "--cov=launchers",
    "--cov-fail-under=35",
]
```

**Lines 210-218 (coverage exclusions):**
```toml
omit = [
    "engines/*/python/*",           # ❌ Excluding engines!
    "engines/physics_engines/*",    # ❌ Excluding engines!
]
```

## 🎯 Expected Behavior

Coverage configuration should be internally consistent - we can't measure coverage for code we've excluded.

## ✅ Proposed Solution

Update `pyproject.toml` lines 172-179 to align with the coverage strategy:

```toml
[tool.pytest.ini_options]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=shared/python",    # ✅ Specific to shared Python code
    "--cov=launchers",         # ✅ Keep launcher coverage
    "--cov-report=term-missing",
    "--cov-report=xml",
    "--cov-report=html",
    "--cov-fail-under=35",
]
```

## 🧪 Testing Plan

1. Run pytest locally: `pytest tests/ --cov=shared/python --cov=launchers`
2. Verify coverage report generates without errors
3. Ensure CI pipeline passes
4. Confirm coverage percentage is accurately calculated

## 📊 Impact

- **Priority:** 🔴 HIGH
- **Effort:** 10 minutes
- **Risk:** Low (documentation/configuration only)
- **Dependencies:** None

## 🔗 Related Issues

- Part of Phase 1: Critical Fixes
- Blocks reliable CI/CD pipeline
- Related to #TBD (Master Tracking Issue)

## ✅ Acceptance Criteria

- [ ] `pyproject.toml` coverage targets match omit patterns
- [ ] CI pytest job completes successfully
- [ ] Coverage report accurately reflects shared/launchers only
- [ ] Documentation updated if needed

---

**Priority:** HIGH | **Phase:** 1 | **Estimated Time:** 10 minutes
