---
name: Remove or track TODO/FIXME comments
about: CI blocks on TODO/FIXME - convert to tracked issues or remove
title: '[TECH-DEBT] Remove or convert TODO/FIXME comments to GitHub issues'
labels: ['tech-debt', 'priority: high', 'ci-cd', 'phase-1']
assignees: ''
---

## 🐛 Problem Description

The CI pipeline **blocks on TODO/FIXME comments** (`.github/workflows/ci-standard.yml:58-63`), but multiple files still contain these placeholders. This causes builds to fail and prevents legitimate code changes.

## 📍 Location

**CI Check:** `.github/workflows/ci-standard.yml` lines 58-63
```yaml
- name: Verify No Placeholders
  run: |
    if grep -rE "TODO|FIXME" shared/python/; then
       echo "::error::Placeholders found. Remove TODOs/FIXMEs or create tracked GitHub issues."
       exit 1
    fi
```

**Files with TODO/FIXME:** (sample from search)
```
/engines/physics_engines/drake/python/swing_plane_integration.py
/engines/physics_engines/mujoco/tools/matlab_utilities/scripts/matlab_quality_check.py
... (8+ files found)
```

## 🎯 Two-Part Solution

### Option A: Convert to GitHub Issues (Preferred)
For each TODO/FIXME:
1. Create a tracked GitHub issue with details
2. Replace inline comment with issue reference
3. Add link to tracking issue

**Before:**
```python
# TODO: Implement async loading for better performance
def load_engine(self):
    ...
```

**After:**
```python
# See issue #123 for async loading implementation
def load_engine(self):
    ...
```

### Option B: Remove if Obsolete
If the TODO is no longer relevant:
- Just delete the comment
- Commit with explanation in message

## 🔍 Audit Process

### Step 1: Find all occurrences
```bash
# Comprehensive search
grep -rn "TODO\|FIXME\|XXX\|HACK" \
  --include="*.py" \
  shared/python/ \
  launchers/ \
  > todo_audit.txt
```

### Step 2: Categorize each item
- **Critical:** Security, correctness issues → Create issues immediately
- **Enhancement:** Feature requests → Create issues, tag as enhancement
- **Obsolete:** Old comments → Delete
- **Documentation:** Missing docs → Create documentation issues

### Step 3: Create issues for keepers
- Use appropriate templates
- Add context from surrounding code
- Link to file/line number

### Step 4: Clean up code
- Replace with issue references or remove
- Update comments to be more specific

## 📋 Example TODO Conversion

**Found TODO:**
```python
# engines/physics_engines/drake/python/swing_plane_integration.py:45
# TODO: Add validation for swing plane parameters
def set_swing_plane(self, angle: float):
    self.angle = angle
```

**Created Issue #125:**
```markdown
Title: Add swing plane parameter validation
- Validate angle range: 0-90 degrees
- Check for NaN/Inf values
- Add unit tests
Location: drake/python/swing_plane_integration.py:45
```

**Updated Code:**
```python
# Parameter validation tracked in #125
def set_swing_plane(self, angle: float):
    self.angle = angle
```

## 🧪 Testing Plan

- [ ] Run CI check locally: `grep -rE "TODO|FIXME" shared/python/`
- [ ] Verify no matches in checked directories
- [ ] Ensure CI pipeline passes
- [ ] All converted TODOs have corresponding issues

## 📊 Impact

- **Priority:** 🔴 HIGH
- **Effort:** 2-3 hours (depends on TODO count)
- **Risk:** Low
- **Benefit:** Unblocks CI, improves issue tracking

## 🔗 Related Issues

- Part of Phase 1: Critical Fixes
- Blocks CI/CD reliability
- Related to #TBD (Master Tracking Issue)

## ✅ Acceptance Criteria

- [ ] All TODO/FIXME in `shared/python/` removed or converted
- [ ] All TODO/FIXME in `launchers/` removed or converted
- [ ] CI check passes: no TODO/FIXME in checked paths
- [ ] Created issues linked from code where appropriate
- [ ] Audit report created: `docs/todo_conversion_log.md`

## 📝 Alternative Approach

If we want to keep inline TODOs for development:

**Update CI to be more lenient:**
```yaml
# Allow TODOs in development but require issue references
- name: Verify TODOs Have Issues
  run: |
    # Check for TODOs without issue references
    if grep -rE "TODO(?!.*#[0-9])" shared/python/; then
       echo "::error::TODOs must reference GitHub issues (e.g., TODO #123)"
       exit 1
    fi
```

---

**Priority:** HIGH | **Phase:** 1 | **Estimated Time:** 2-3 hours
