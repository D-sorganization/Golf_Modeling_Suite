---
name: Add CI check for duplicate files
about: Prevent code duplication with automated detection
title: '[CI] Add automated duplicate file detection to CI pipeline'
labels: ['ci-cd', 'priority: high', 'tooling', 'phase-1']
assignees: ''
---

## 🎯 Problem Description

The codebase has **significant file duplication** that causes maintenance nightmares:
- **8 identical copies** of `matlab_quality_check.py`
- **3 duplicate** double pendulum implementations
- **10 different** `constants.py` files with overlapping content

Bug fixes must be applied multiple times, and versions inevitably drift.

## 📍 Examples of Duplication

### matlab_quality_check.py (8 copies!)
```
/tools/matlab_utilities/scripts/matlab_quality_check.py (canonical)
/engines/physics_engines/mujoco/tools/matlab_utilities/scripts/matlab_quality_check.py
/engines/physics_engines/pinocchio/tools/matlab_utilities/scripts/matlab_quality_check.py
/engines/physics_engines/drake/tools/matlab_utilities/scripts/matlab_quality_check.py
/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab_utilities/scripts/matlab_quality_check.py
/engines/Simscape_Multibody_Models/2D_Golf_Model/tools/matlab_utilities/scripts/matlab_quality_check.py
/engines/pendulum_models/tools/matlab_utilities/scripts/matlab_quality_check.py
... (8 total)
```

### constants.py (10 files with overlap)
```
/shared/python/constants.py (81 lines - canonical)
/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/constants.py (20 lines)
/engines/physics_engines/mujoco/python/src/constants.py
/engines/physics_engines/pinocchio/python/src/constants.py
... (10 total)
```

## ✅ Proposed Solution

Create automated duplicate detection that runs in CI:

### Step 1: Create duplicate detection script

**File:** `scripts/check_duplicates.py`
```python
#!/usr/bin/env python3
"""Detect duplicate files in the codebase."""

import hashlib
from pathlib import Path
from collections import defaultdict
import sys

def calculate_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()

def find_duplicates(
    root: Path,
    patterns: list[str] = ["*.py"],
    exclude_patterns: list[str] = ["*test*", "__pycache__", ".git"]
) -> dict[str, list[Path]]:
    """Find duplicate files by content hash."""
    hash_to_files = defaultdict(list)

    for pattern in patterns:
        for file_path in root.rglob(pattern):
            # Skip excluded patterns
            if any(excl in str(file_path) for excl in exclude_patterns):
                continue

            file_hash = calculate_hash(file_path)
            hash_to_files[file_hash].append(file_path)

    # Return only duplicates (hash with >1 file)
    return {h: files for h, files in hash_to_files.items() if len(files) > 1}

def main():
    root = Path(__file__).parent.parent
    duplicates = find_duplicates(root)

    if duplicates:
        print("❌ DUPLICATE FILES FOUND:")
        for file_hash, files in duplicates.items():
            print(f"\n🔄 {len(files)} identical copies:")
            for f in files:
                print(f"   - {f.relative_to(root)}")

        print(f"\n\n❌ Found {len(duplicates)} sets of duplicate files")
        print("Fix: Consolidate to single canonical location and use imports/symlinks")
        sys.exit(1)
    else:
        print("✅ No duplicate files found")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Step 2: Add to CI pipeline

**File:** `.github/workflows/ci-standard.yml`

Add after the quality gate:
```yaml
- name: Check for Duplicate Files
  run: |
    python scripts/check_duplicates.py
```

### Step 3: Add configuration file

**File:** `scripts/duplicate_check_config.yaml`
```yaml
# Configuration for duplicate file detection
patterns:
  - "*.py"
  - "*.yaml"
  - "*.json"

exclude_patterns:
  - "*test*"
  - "__pycache__"
  - ".git"
  - "docs/archive"
  - "*/Archive/*"
  - "*/legacy/*"

# Files we know are duplicated and need cleanup
known_duplicates:
  matlab_quality_check.py:
    canonical: "tools/matlab_utilities/scripts/matlab_quality_check.py"
    duplicates: 7
    tracked_issue: "#TBD"
```

## 🔄 Handling Legitimate Duplicates

Some files might need to be duplicated (e.g., vendored dependencies). Options:

1. **Allowlist in config:**
```yaml
allowed_duplicates:
  - "vendor/third_party/**/*.py"
```

2. **Use symlinks:**
```bash
# Keep canonical, link from engines
ln -s ../../../../tools/matlab_utilities/scripts/matlab_quality_check.py \
      engines/mujoco/tools/matlab_utilities/scripts/matlab_quality_check.py
```

3. **Import instead of copy:**
```python
# Instead of copying, import from shared location
from tools.matlab_utilities.scripts.matlab_quality_check import run_check
```

## 🧪 Testing Plan

- [ ] Run script locally: `python scripts/check_duplicates.py`
- [ ] Verify it detects known duplicates
- [ ] Add to CI and test on pull request
- [ ] Ensure it doesn't flag legitimate files

## 📊 Impact

- **Priority:** 🔴 HIGH
- **Effort:** 2-3 hours
- **Risk:** Low (detection only, doesn't modify code)
- **Benefit:**
  - Prevents new duplicates
  - Highlights existing duplicates for cleanup
  - Improves code maintainability

## 🔗 Related Issues

- Part of Phase 1: Critical Fixes
- Blocks #TBD (Consolidate duplicate constants)
- Blocks #TBD (Consolidate pendulum implementations)
- Related to #TBD (Master Tracking Issue)

## ✅ Acceptance Criteria

- [ ] `scripts/check_duplicates.py` created and tested
- [ ] Script detects known duplicates (matlab_quality_check.py)
- [ ] Configuration file supports exclusions
- [ ] CI job added to `.github/workflows/ci-standard.yml`
- [ ] CI fails when duplicates are found
- [ ] Documentation updated in CONTRIBUTING.md

## 📝 Future Enhancements

- Detect partial duplicates (code clones) using tools like `jscpd` or `radon`
- Integrate with code review bot to flag duplicates in PRs
- Generate deduplication suggestions automatically

---

**Priority:** HIGH | **Phase:** 1 | **Estimated Time:** 2-3 hours
