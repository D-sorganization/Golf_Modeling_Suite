# Test Suite Mocking Remediation - Issue #2712

## Problem Statement

The test suite violates CLAUDE.md by using module-level `sys.modules` mocking:

```python
# ❌ WRONG: Pollutes sys.modules for entire test run
sys.modules["pydrake"] = MagicMock()

def test_something():
    pass  # This test gets mock, but so do ALL subsequent tests!
```

This causes:

1. Test pollution across the suite
2. False-green CI (mocked tests pass but real code doesn't work)
3. Inability to verify engine integration
4. Hidden failures in downstream tests

## Flagged Violations

Files with module-level sys.modules mocking:

- `tests/unit/engines/drake/test_drake_visualizer.py:14-15`
- `tests/unit/engines/drake/test_induced_acceleration.py:13-14`
- `tests/unit/engines/mujoco/conftest.py:13-15`
- `tests/unit/engines/opensim/test_muscle_conditioning.py:37`
- `tests/unit/test_optimize_arm.py:16-17,37,41` (multiple violations)

## Solution: Use patch.dict() Decorator

### Pattern for Individual Tests

```python
from unittest.mock import patch, MagicMock

@patch.dict("sys.modules", {"pydrake": MagicMock()})
def test_something():
    # Mock is ONLY active for this test
    # Auto-cleans up after test execution
    pass
```

### Pattern for Test Classes/Fixtures

```python
from unittest.mock import patch

class TestDrake:
    @patch.dict("sys.modules", {"pydrake": MagicMock()})
    def test_method(self):
        pass
```

## Remediation Priority

### Phase 1 (CRITICAL): Drake Engine

- test_drake_visualizer.py (blocks integration tests)
- test_induced_acceleration.py (core physics validation)
- Recommend: Patch each @test method individually

### Phase 2 (HIGH): Optimization/Planning

- test_optimize_arm.py (multiple mocks - 3 violations)
- Recommend: Extract to conftest fixture using patch.dict

### Phase 3 (MEDIUM): Other Engines

- mujoco/conftest.py (affects multiple tests)
- opensim/test_muscle_conditioning.py
- Recommend: Move to fixtures with proper scoping

## Testing the Fix

After applying patch.dict:

1. Run affected test file individually: `pytest tests/unit/engines/drake/test_drake_visualizer.py -v`
2. Run full suite: `pytest tests/ -n auto`
3. Verify no test pollution: Each test runs independently
4. Check CI-green status: All tests validate real dependencies

## References

- CLAUDE.md: "Never sys.modules["pydrake"] = MagicMock() at module level"
- unittest.mock.patch.dict documentation
- Related: Tests that check physics accuracy (#2712)
