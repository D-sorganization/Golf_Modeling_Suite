---
name: Consolidate duplicate constants files
about: Eliminate 10 different constants.py files with overlapping definitions
title: '[REFACTOR] Consolidate 10 constants.py files into shared module'
labels: ['refactoring', 'priority: medium', 'code-quality', 'phase-2']
assignees: ''
---

## 🎯 Problem Description

Found **10 different `constants.py` files** across the codebase with:
- Duplicate constant definitions
- Inconsistent naming (`GRAVITY_M_S2` vs `GRAVITY_STANDARD_M_S2`)
- No single source of truth
- Risk of values drifting between engines

## 📍 Current State

```
shared/python/constants.py (81 lines) ✅ CANONICAL
├── GRAVITY_M_S2 = 9.80665
├── GOLF_BALL_MASS_KG = 0.04593
├── PI, E, DEG_TO_RAD, etc.
└── Golf-specific constants

engines/physics_engines/mujoco/.../constants.py (20 lines)
├── GRAVITY_STANDARD_M_S2 = 9.80665  ❌ Different name!
├── PI, PI_HALF, PI_QUARTER
└── SPATIAL_DIM = 6

engines/physics_engines/pinocchio/.../constants.py
engines/physics_engines/drake/.../constants.py
engines/Simscape_Multibody_Models/2D_Golf_Model/.../constants.py
engines/Simscape_Multibody_Models/3D_Golf_Model/.../constants.py
engines/pendulum_models/.../constants.py
... (10 total)
```

## ✅ Proposed Solution

### Strategy: Consolidate to shared + engine-specific

**Keep canonical:** `shared/python/constants.py` (already comprehensive!)

**Engine-specific constants:** Only truly engine-unique values

```python
# shared/python/constants.py (CANONICAL)
"""Physical and mathematical constants - SINGLE SOURCE OF TRUTH."""
GRAVITY_M_S2: float = 9.80665  # Use this everywhere!
GOLF_BALL_MASS_KG: float = 0.04593
PI: float = math.pi
# ... all common constants

# engines/mujoco/python/mujoco_humanoid_golf/mujoco_constants.py
"""MuJoCo-specific constants ONLY."""
from shared.python.constants import GRAVITY_M_S2, PI  # Import common

# Only MuJoCo-unique values
SPATIAL_DIM: int = 6  # MuJoCo spatial vectors
MUJOCO_MAX_CONTACTS: int = 100
```

## 🔄 Migration Steps

### Step 1: Audit all constants files
```bash
# Create comprehensive inventory
python scripts/audit_constants.py > constants_inventory.txt
```

**Script:** `scripts/audit_constants.py`
```python
#!/usr/bin/env python3
"""Audit all constants.py files to find duplicates."""
import ast
from pathlib import Path

def extract_constants(file_path):
    """Parse Python file and extract constant definitions."""
    tree = ast.parse(file_path.read_text())
    constants = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = ast.unparse(node.value)
    return constants

# Find all constants.py files
root = Path(".")
for const_file in root.rglob("constants.py"):
    if ".git" in str(const_file):
        continue

    print(f"\n{'='*60}")
    print(f"File: {const_file}")
    print(f"{'='*60}")

    constants = extract_constants(const_file)
    for name, value in sorted(constants.items()):
        print(f"{name:40} = {value}")
```

### Step 2: Identify duplicates and conflicts
```python
# scripts/find_constant_conflicts.py
"""Find constants with same name but different values."""
from collections import defaultdict

all_constants = defaultdict(list)

# Populate from audit
# Find conflicts: same name, different values
conflicts = {
    name: values
    for name, values in all_constants.items()
    if len(set(values)) > 1  # Multiple different values!
}

for name, values in conflicts.items():
    print(f"⚠️  CONFLICT: {name}")
    for value, file in values:
        print(f"   {value:20} in {file}")
```

### Step 3: Migrate each engine

**Example: MuJoCo engine**
```python
# BEFORE: engines/mujoco/.../constants.py
GRAVITY_STANDARD_M_S2: float = 9.80665
PI: float = math.pi
SPATIAL_DIM: int = 6

# AFTER: engines/mujoco/.../mujoco_constants.py
from shared.python.constants import GRAVITY_M_S2 as GRAVITY_STANDARD_M_S2, PI

# Only MuJoCo-specific (not in shared)
SPATIAL_DIM: int = 6  # MuJoCo spatial vector dimension
```

**Update imports throughout MuJoCo:**
```python
# Old
from .constants import GRAVITY_STANDARD_M_S2

# New
from shared.python.constants import GRAVITY_M_S2 as GRAVITY_STANDARD_M_S2
# OR better: unify naming
from shared.python.constants import GRAVITY_M_S2
```

### Step 4: Standardize naming
Choose canonical names and update all references:

| Old Names | Canonical Name | Decision |
|-----------|----------------|----------|
| `GRAVITY_M_S2`, `GRAVITY_STANDARD_M_S2` | `GRAVITY_M_S2` | Shorter, clearer |
| `PI`, `pi` | `PI` | Follow PEP 8 |
| Various units formats | Add `_UNITS` suffix | `GRAVITY_M_S2` (units in name) |

### Step 5: Delete redundant files
After migration and testing:
```bash
# Remove old constants files
git rm engines/*/constants.py
git rm engines/*/*/constants.py

# Keep only:
# - shared/python/constants.py (canonical)
# - engines/*/XXX_constants.py (engine-specific only)
```

## 🧪 Testing Strategy

### Create constants usage tests
```python
# tests/unit/test_constants_consistency.py
"""Verify constants are used consistently across engines."""

def test_gravity_constant_used_everywhere():
    """All engines should use canonical GRAVITY_M_S2."""
    # Search codebase for gravity usage
    # Ensure no hardcoded 9.80665 values
    # Ensure all import from shared.python.constants

def test_no_duplicate_constant_files():
    """Should only have shared constants + engine-specific."""
    constants_files = list(Path(".").rglob("constants.py"))
    # Only shared/python/constants.py allowed
    assert len([f for f in constants_files if "shared/python" in str(f)]) == 1

def test_physical_constants_match_references():
    """Verify constants match published values."""
    from shared.python.constants import GRAVITY_M_S2
    assert abs(GRAVITY_M_S2 - 9.80665) < 1e-6  # ISO 80000-3:2006
```

### Migration validation
```bash
# Run all tests to ensure nothing broke
pytest tests/

# Verify imports resolve correctly
python -c "from shared.python.constants import GRAVITY_M_S2; print(GRAVITY_M_S2)"
```

## 📋 Migration Checklist

- [ ] Run audit script to inventory all constants
- [ ] Identify conflicts (same name, different values)
- [ ] Resolve conflicts and choose canonical names
- [ ] Update `shared/python/constants.py` with all common constants
- [ ] Create engine-specific constant files (if needed)
- [ ] Migrate MuJoCo imports
- [ ] Migrate Drake imports
- [ ] Migrate Pinocchio imports
- [ ] Migrate Simscape imports
- [ ] Migrate Pendulum imports
- [ ] Update all references throughout codebase
- [ ] Add constant usage tests
- [ ] Delete old constants.py files
- [ ] Update documentation

## 📊 Impact

- **Priority:** 🟡 MEDIUM
- **Effort:** 1-2 weeks
- **Risk:** Medium (affects all engines)
- **Benefit:**
  - Single source of truth
  - Consistent naming
  - Easier maintenance
  - Reduces errors

## ⚠️ Breaking Changes

- Import paths will change for all engines
- Some constant names will change (standardization)
- Need to update all references

## 🔗 Related Issues

- Part of Phase 2: Technical Debt Reduction
- Blocked by #TBD (Duplicate file detection)
- Related to #TBD (Master Tracking Issue)

## ✅ Acceptance Criteria

- [ ] Only 1 canonical `shared/python/constants.py`
- [ ] Engine-specific constants in separate files (if needed)
- [ ] All common constants imported from shared
- [ ] No duplicate constant definitions
- [ ] Consistent naming across all engines
- [ ] All tests pass
- [ ] Documentation updated with constant usage guide

---

**Priority:** MEDIUM | **Phase:** 2 | **Estimated Time:** 1-2 weeks
