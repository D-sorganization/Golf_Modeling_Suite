# AGENTS.md — Shared Infrastructure Directory & Discovery Workflow

This document prevents code duplication by guiding agents (Claude, human, or otherwise) to discover existing infrastructure before writing new code.

## Quick Start: Before You Write New Code

**Always follow this 5-step discovery workflow:**

1. **Grep `src/shared/`** for the concept:
   ```bash
   grep -r "forward_kinematics" src/shared/python/
   grep -r "reference_pose" src/shared/python/
   ```

2. **Grep `src/engines/`, `src/tools/`, `src/launchers/`, `src/api/`** for existing implementations.

3. **Read matching `__init__.py`** files to understand the public API surface.

4. **Read relevant docs** in `docs/` (e.g., `docs/motion_matching/`, `docs/development/agents.md`).

5. **Only then** propose new code.

---

## Section A — Discovery Workflow Details

### A.1 Grep Patterns by Concept

| Concept | Grep Target | Typical Location |
|---------|-------------|------------------|
| Forward kinematics | `forward_kinematics` | `src/shared/python/motion_matching/diagnostics/` |
| Reference pose | `reference_golfer_setup` | `src/shared/python/motion_matching/diagnostics/reference_pose.py` |
| Skeleton rendering | `equalize_3d_axes`, `draw_segments` | `src/shared/python/motion_matching/diagnostics/_skeleton_render.py` |
| Mocap loaders | `load_club_target`, `cm_to_meters` | `src/shared/python/club_data/` |
| Plot helpers | `plot_*`, `theme` | `src/shared/python/plot_theme/`, `src/shared/python/theme/` |
| Physics engines | `PhysicsEngine`, `simulate` | `src/shared/python/engine_core/` |
| Launchers | `BaseLauncher`, `register_tile` | `src/launchers/base.py` |

### A.2 Reading `__init__.py` for Public API

Each shared module exports its public API in `__init__.py`. Example:

```python
# src/shared/python/motion_matching/diagnostics/__init__.py
from .forward_kinematics import forward_kinematics
from .reference_pose import reference_golfer_setup
from ._skeleton_render import equalize_3d_axes, draw_segments

__all__ = [
    "forward_kinematics",
    "reference_golfer_setup",
    "equalize_3d_axes",
    "draw_segments",
]
```

### A.3 Documentation Locations

| Doc Path | Purpose |
|----------|---------|
| `docs/motion_matching/` | Motion matching algorithms, FK, IK |
| `docs/development/agents.md` | Agent workflow and policies |
| `docs/api/` | API reference documentation |
| `docs/tutorials/` | How-to guides |

---

## Section B — Shared Infrastructure Directory

### B.1 Core Physics Engine Layer

**Location:** `src/shared/python/engine_core/`

The `PhysicsEngine` protocol defines the interface all physics engines implement.

| Symbol | Purpose |
|--------|---------|
| `PhysicsEngine` | Abstract base class for all engines |
| `EngineConfig` | Configuration dataclass |
| `SimulationResult` | Standardized output type |

### B.2 Motion Matching

**Location:** `src/shared/python/motion_matching/`

Comprehensive motion matching infrastructure including FK, IK, diagnostics, and cost functions.

#### Diagnostics Submodule

**Location:** `src/shared/python/motion_matching/diagnostics/`

| Module | Public Symbols | Purpose |
|--------|----------------|---------|
| `forward_kinematics.py` | `forward_kinematics(angles) -> dict` | Compute Cartesian joint positions from Simulink-style angle dict |
| `reference_pose.py` | `reference_golfer_setup() -> dict` | Canonical address-pose joint angles |
| `_skeleton_render.py` | `equalize_3d_axes(ax)`, `draw_segments(ax, positions)`, `draw_delta_arrows(ax, start, end)` | 3D visualization helpers |
| `club_target.py` | `ClubTarget`, `load_target()` | Club target data structures |
| `cost.py` | `CostFunction`, `compute_cost()` | Motion matching cost functions |
| `metrics.py` | `compute_metrics()` | Performance metrics |

#### Other Submodules

| Submodule | Purpose |
|-----------|---------|
| `dataset/` | Motion capture dataset loaders |
| `inverse/` | Inverse kinematics solvers |
| `loaders/` | Generic data loaders |
| `surrogate/` | Surrogate models for optimization |

### B.3 Pose Editor

**Location:** `src/shared/python/pose_editor/`

Interactive joint-angle editor for configuring character poses.

| Symbol | Purpose |
|--------|---------|
| `PoseEditor` | PyQt6-based interactive editor |
| `PosePreset` | Saved pose configurations |

### B.4 Club Data

**Location:** `src/shared/python/club_data/`

Mocap target loaders for C3D, xlsx, and JSON formats.

| Module | Purpose |
|--------|---------|
| `c3d_loader.py` | Load C3D motion capture files |
| `excel_loader.py` | Load Excel target data |
| `json_loader.py` | Load JSON configurations |
| `unit_conversion.py` | cm/inches/meters conversion utilities |

### B.5 Theme

**Location:** `src/shared/python/theme/`

Colors, typography, and QSS stylesheets for PyQt6 applications.

| Symbol | Purpose |
|--------|---------|
| `COLOR_PALETTE` | Standardized color scheme |
| `TYPOGRAPHY` | Font specifications |
| `QSS_STYLES` | Qt stylesheet definitions |

### B.6 Plot Theme

**Location:** `src/shared/python/plot_theme/`

Matplotlib styling and plot configuration.

| Symbol | Purpose |
|--------|---------|
| `apply_theme(ax)` | Apply standard theme to axes |
| `PlotStyle` | Enum of plot styles |

### B.7 Base Launcher

**Location:** `src/launchers/base.py`

**Purpose:** ONLY for grid-of-tiles launcher infrastructure.

| Symbol | Purpose |
|--------|---------|
| `BaseLauncher` | Main launcher window class |
| `TileConfig` | Tile configuration dataclass |
| `launch_tile(id)` | Launch a registered tile |

### B.8 Rust Core

**Location:** `rust_core/upstream-physics/`

Performance-critical kernels reused by Python and WASM.

| Crate | Purpose |
|-------|---------|
| `upstream-physics` | RK4 integrator, aerodynamics models |

**Build:** `maturin develop`

---

## Section C — Where New Code Goes

### Decision Tree

```
Is the code...?
│
├─ Used by ONE engine only?
│  └─→ src/engines/<engine>/python/
│
├─ Used by 2+ engines?
│  └─→ src/shared/python/<topic>/
│
├─ Standalone desktop tool (PyQt6 QMainWindow)?
│  └─→ src/tools/<tool_name>/
│      └─→ Register in src/config/models.yaml
│
├─ Inner-loop math kernel reused by Python AND WASM?
│  └─→ rust_core/<crate>/
│
└─ Engine-specific MATLAB code?
   └─→ src/engines/<engine>/matlab/
```

### Examples

| New Feature | Correct Location |
|-------------|------------------|
| Drake-specific simulator wrapper | `src/engines/physics_engines/drake/python/` |
| New motion matching cost function | `src/shared/python/motion_matching/cost.py` |
| Video analysis GUI tool | `src/tools/video_analyzer/` |
| SIMD-optimized RK4 kernel | `rust_core/upstream-physics/` |
| MATLAB script for Simscape model | `src/engines/Simscape_Multibody_Models/.../matlab/` |

---

## Section D — Tile-Launcher Contract

### Registering a New Tile

Tiles are registered in `src/config/models.yaml`:

```yaml
- id: "my_new_tool"
  name: "My Tool"
  description: "Brief description of what this tool does"
  type: "custom"
  path: "src/tools/my_new_tool/__main__.py"
  launcher:
    category: "tools"
    logo: "tool"
    status: "stable"  # or "experimental", "deprecated"
```

### Tile Requirements

1. **Entry point:** `__main__.py` with `if __name__ == "__main__":` block
2. **Launchable via:** `python -m src.tools.my_new_tool`
3. **GUI tools:** Must be PyQt6 `QMainWindow` subclass
4. **Dependencies:** Document in tool's `README.md` and add to `pyproject.toml` if needed

### Existing Tiles

See `src/config/models.yaml` for the complete list. Primary tiles include:

- MuJoCo, Drake, Pinocchio, OpenSim, MyoSuite (physics engines)
- MATLAB Simscape Models
- Model Explorer, Video Analyzer, Data Explorer (tools)

---

## Section E — Tests

### Test Locations

| Test Type | Location |
|-----------|----------|
| Unit tests | `tests/unit/<area>/` |
| Integration tests | `tests/integration/` |
| Live simulation tests | `tests/live_simulation/` |
| Benchmark tests | `tests/benchmarks/` |

### Test Markers

| Marker | Purpose |
|--------|---------|
| `unit` | Fast, isolated unit tests |
| `integration` | Multi-component integration tests |
| `slow` | Tests taking >1 second |
| `live_simulation` | Tests requiring actual simulation |
| `requires_gl` | Tests requiring OpenGL/GUI |
| `headless_safe` | Tests safe to run headless |
| `benchmark` | Performance benchmarks |
| `scientific` | Scientifically validated tests |

### Running Tests

```bash
# Full test suite
python3 -m pytest -n auto --timeout=60

# Unit tests only
python3 -m pytest -m unit -n auto --timeout=60

# Exclude slow and live simulation tests
python3 -m pytest -m "not slow and not live_simulation" -n auto --timeout=60

# With coverage
python3 -m pytest -n auto --timeout=60 --cov=src --cov-report=html
```

### Skipping GUI Dependencies

When optional GUI deps may be missing:

```python
import pytest

@pytest.mark.requires_gl
def test_gui_component():
    pytest.importorskip("PyQt6")
    # ... test code
```

---

## Section F — When to Use Rust

### Criteria for Rust Implementation

Use Rust when **ANY** of these criteria are met:

1. **Shared kernel reused by Python AND WASM**
   - Example: `rust_core/upstream-physics/` provides RK4 integrator used by both

2. **Sub-millisecond inner loops (verified by profiling)**
   - Profile first with `cProfile` or `line_profiler`
   - Only optimize hot paths after measurement

3. **Numerical kernels with tight loops**
   - Matrix operations, vector math, iterative solvers

### When NOT to Use Rust

Do **NOT** use Rust for:

- GUI tools (PyQt6 is the standard)
- One-off scripts or utilities
- Code not in hot paths (profile first!)
- Configuration or data files

### Building Rust Extensions

```bash
# Local development
maturin develop

# Release build
maturin build --release
```

---

## Appendix: Common Reinventions to Avoid

Based on historical analysis, these are commonly reinvented:

| Reinvention | Existing Solution | Location |
|-------------|-------------------|----------|
| Hand-tuned fallback skeletons | `forward_kinematics(reference_golfer_setup())` | `motion_matching/diagnostics/forward_kinematics.py` |
| Hardcoded address-pose angles | `reference_golfer_setup()` | `motion_matching/diagnostics/reference_pose.py` |
| Custom 3D axis equalization | `equalize_3d_axes(ax)` | `motion_matching/diagnostics/_skeleton_render.py` |
| Cm/inches unit handling | `unit_conversion.py` utilities | `club_data/` |
| Custom plot boilerplate | `apply_theme(ax)` | `plot_theme/` |

---

## Related Files

- `CLAUDE.md` — Agent policy and coding standards
- `docs/development/agents.md` — Extended agent documentation
- `src/config/models.yaml` — Tile registration
- `pyproject.toml` — Project configuration and dependencies