---
name: Consolidate requirements.txt files
about: Eliminate 20+ duplicate requirements files into single pyproject.toml
title: '[REFACTOR] Consolidate 20+ requirements.txt files into pyproject.toml'
labels: ['refactoring', 'priority: high', 'dependencies', 'phase-1']
assignees: ''
---

## 🎯 Problem Description

The project has **20+ scattered requirements.txt files** across different engine directories, causing:
- Dependency version drift between engines
- Difficult dependency upgrades
- Risk of conflicting package versions
- Confusion about canonical dependencies

## 📍 Current State

Found requirements files in:
```
/requirements.txt (main)
/engines/physics_engines/mujoco/python/requirements.txt
/engines/physics_engines/mujoco/docker/requirements.txt
/engines/physics_engines/pinocchio/python/requirements.txt
/engines/physics_engines/pinocchio/python/requirements-ci.txt
/engines/physics_engines/drake/python/requirements.txt
/engines/physics_engines/drake/python/requirements-ci.txt
/engines/physics_engines/drake/requirements.txt
/engines/Simscape_Multibody_Models/3D_Golf_Model/python/requirements.txt
/engines/Simscape_Multibody_Models/2D_Golf_Model/python/requirements.txt
/engines/pendulum_models/python/requirements.txt
/engines/pendulum_models/Pendulum Models/Double Pendulum Model/requirements.txt
/engines/pendulum_models/Pendulum Models/Pendulums_Model/requirements.txt
/shared/python/requirements.txt
... (7+ more)
```

## ✅ Proposed Solution

**We already have a comprehensive `pyproject.toml`** with optional dependencies! Just need to:

1. **Consolidate all requirements into root `pyproject.toml`**
   - Already has `[project.optional-dependencies]` section
   - Merge engine-specific deps into appropriate groups

2. **Update pyproject.toml optional dependencies:**
```toml
[project.optional-dependencies]
dev = ["pytest>=8.2.1", "ruff==0.5.0", ...]
engines = ["drake>=1.22.0", "pin>=2.6.0", ...]
mujoco = ["mujoco>=3.2.3", "dm-control>=1.0.0"]
drake = ["drake>=1.22.0"]
pinocchio = ["pin>=2.6.0", "pin-pink>=1.0.0"]
all = ["golf-modeling-suite[dev,engines,analysis]"]
```

3. **Update installation instructions:**
```bash
# Core installation
pip install -r requirements.txt  # Just installs from pyproject.toml

# Development setup
pip install -e .[dev,all]

# Engine-specific
pip install -e .[mujoco]
pip install -e .[drake]
```

4. **Delete redundant requirements.txt files**
   - Keep only root `requirements.txt` (which just does `-e .`)
   - Remove all engine-specific requirements files

5. **Update CI/CD workflows**
   - `.github/workflows/ci-standard.yml` already uses root requirements

## 🔄 Migration Plan

### Step 1: Audit all requirements files
```bash
# Create consolidated dependency list
find . -name "requirements*.txt" -exec echo "=== {} ===" \; -exec cat {} \;
```

### Step 2: Merge into pyproject.toml
- Add missing dependencies to appropriate optional groups
- Resolve version conflicts (use most restrictive)

### Step 3: Test installation
```bash
# Test each combination
pip install -e .
pip install -e .[dev]
pip install -e .[mujoco]
pip install -e .[all]
```

### Step 4: Update documentation
- `README.md` installation section
- `docs/user_guide/installation.md`
- Engine-specific docs

### Step 5: Clean up
```bash
# Remove redundant files (after validation)
git rm engines/*/requirements*.txt
git rm engines/*/*/requirements*.txt
```

## 🧪 Testing Plan

- [ ] Fresh virtual environment installation succeeds
- [ ] Each engine can be installed independently
- [ ] `pip install -e .[all]` installs everything
- [ ] CI pipeline passes with updated installation
- [ ] Docker builds still work (update Dockerfiles)

## 📊 Impact

- **Priority:** 🔴 HIGH
- **Effort:** 2-4 hours
- **Risk:** Medium (could break installations if not tested)
- **Benefits:**
  - Single source of truth for dependencies
  - Easier version upgrades
  - Clearer dependency relationships
  - Reduced repository clutter

## ⚠️ Breaking Changes

- Old commands like `pip install -r engines/mujoco/requirements.txt` will fail
- Need to update documentation and CI scripts

## 🔗 Related Issues

- Part of Phase 1: Critical Fixes
- Related to #TBD (Master Tracking Issue)
- Prerequisite for dependency version management

## ✅ Acceptance Criteria

- [ ] All dependencies consolidated into `pyproject.toml`
- [ ] Root `requirements.txt` contains only `-e .`
- [ ] All engine-specific `requirements*.txt` files deleted
- [ ] Fresh installation tested for all configurations
- [ ] Documentation updated (README, installation guide)
- [ ] CI/CD updated if needed
- [ ] Docker builds updated if needed

---

**Priority:** HIGH | **Phase:** 1 | **Estimated Time:** 2-4 hours
