---
name: Refactor large GUI files
about: Break down monolithic GUI files into smaller, maintainable modules
title: '[REFACTOR] Break down large GUI files (3,933+ lines) into smaller modules'
labels: ['refactoring', 'priority: medium', 'code-quality', 'phase-2']
assignees: ''
---

## 🎯 Problem Description

Several GUI files violate the **Single Responsibility Principle** and have grown to unmaintainable sizes:

| File | Lines | Issue |
|------|-------|-------|
| `advanced_gui.py` | **3,933** | ⚠️ Massive monolith |
| `models.py` | 1,624 | Multiple model classes |
| `sim_widget.py` | 1,580 | Mixed concerns |
| `Motion_Capture_Plotter.py` | 1,495 | Plotting + data + UI |
| `linkage_mechanisms/__init__.py` | 1,360 | Should be split |

**Issues caused:**
- Hard to test individual components
- High merge conflict probability
- Difficult code review
- Tight coupling
- Hard to reuse components

## 📍 Location

**Primary target:** `engines/physics_engines/mujoco/python/mujoco_humanoid_golf/advanced_gui.py`

## ✅ Proposed Refactoring

### Before (monolithic structure):
```
advanced_gui.py (3,933 lines)
├── Main window class
├── Simulation controls
├── Visualization renderer
├── Data plotters
├── Parameter panels
├── Menu system
├── Toolbar logic
├── State management
├── File I/O
└── ... everything else
```

### After (modular structure):
```
gui/
├── __init__.py
├── main_window.py (300-400 lines)
│   └── AdvancedGUI (coordinates components)
├── widgets/
│   ├── __init__.py
│   ├── simulation_panel.py (200-300 lines)
│   ├── control_panel.py (200-300 lines)
│   ├── parameter_panel.py (200-300 lines)
│   └── toolbar.py (150-200 lines)
├── visualization/
│   ├── __init__.py
│   ├── renderer.py (300-400 lines)
│   ├── camera_controls.py (150-200 lines)
│   └── scene_manager.py (200-300 lines)
├── plotting/
│   ├── __init__.py
│   ├── time_series_plotter.py (200-300 lines)
│   ├── phase_space_plotter.py (200-300 lines)
│   └── data_exporter.py (150-200 lines)
├── models/
│   ├── __init__.py
│   ├── state_manager.py (200-300 lines)
│   ├── simulation_config.py (150-200 lines)
│   └── data_models.py (200-300 lines)
└── io/
    ├── __init__.py
    ├── file_operations.py (200-300 lines)
    └── session_manager.py (150-200 lines)
```

## 🔄 Refactoring Process

### Phase 1: Analysis
1. **Map dependencies** within `advanced_gui.py`
2. **Identify logical boundaries** (UI, data, rendering, etc.)
3. **Create dependency graph** to find coupling
4. **Plan extraction order** (least coupled first)

### Phase 2: Extract Classes
```python
# Step 1: Extract data models (no UI dependencies)
# advanced_gui.py → models/simulation_config.py
class SimulationConfig:
    """Configuration state for simulation parameters."""
    def __init__(self):
        self.timestep = 0.001
        self.duration = 10.0
        # ... extracted from AdvancedGUI

# Step 2: Extract widgets (depend on models)
# advanced_gui.py → widgets/parameter_panel.py
class ParameterPanel(QWidget):
    """Panel for adjusting simulation parameters."""
    def __init__(self, config: SimulationConfig):
        super().__init__()
        self.config = config
        self._setup_ui()
        # ... extracted from AdvancedGUI
```

### Phase 3: Update Main Window
```python
# gui/main_window.py
from .widgets import SimulationPanel, ControlPanel, ParameterPanel
from .models import StateManager
from .visualization import Renderer

class AdvancedGUI(QMainWindow):
    """Main application window coordinating components."""

    def __init__(self):
        super().__init__()
        # Now much cleaner!
        self.state_manager = StateManager()
        self.simulation_panel = SimulationPanel(self.state_manager)
        self.control_panel = ControlPanel(self.state_manager)
        self.renderer = Renderer(self.state_manager)
        self._setup_layout()

    def _setup_layout(self):
        """Compose UI from components."""
        # ... simplified layout code
```

### Phase 4: Testing
- Add unit tests for each extracted component
- Ensure existing integration tests still pass
- Verify no regression in functionality

## 🧪 Testing Strategy

### Before refactoring:
```bash
# Capture current behavior as baseline
pytest tests/integration/test_advanced_gui.py --baseline
```

### During refactoring:
```python
# Add unit tests for extracted components
# tests/unit/gui/test_parameter_panel.py
def test_parameter_panel_updates_config():
    config = SimulationConfig()
    panel = ParameterPanel(config)
    panel.set_timestep(0.002)
    assert config.timestep == 0.002
```

### After refactoring:
```bash
# Verify behavior unchanged
pytest tests/integration/test_advanced_gui.py --compare-to-baseline
```

## 📊 Benefits

- **Testability:** Each component can be unit tested independently
- **Reusability:** Extracted widgets can be used in other GUIs
- **Maintainability:** Easier to locate and fix bugs
- **Collaboration:** Multiple developers can work without conflicts
- **Code Review:** Smaller, focused files easier to review

## 📋 Implementation Checklist

### advanced_gui.py (3,933 lines)
- [ ] Create new `gui/` module structure
- [ ] Extract data models → `models/`
- [ ] Extract widgets → `widgets/`
- [ ] Extract visualization → `visualization/`
- [ ] Extract plotting → `plotting/`
- [ ] Extract I/O → `io/`
- [ ] Update main window to compose components
- [ ] Add unit tests for each module
- [ ] Update integration tests
- [ ] Update documentation
- [ ] Delete old monolithic file

### models.py (1,624 lines)
- [ ] Analyze model classes
- [ ] Create `models/` submodules
- [ ] Extract one model class per file
- [ ] Add tests
- [ ] Update imports

### sim_widget.py (1,580 lines)
- [ ] Separate simulation logic from UI
- [ ] Extract widget components
- [ ] Add tests
- [ ] Update references

## ⚠️ Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing code | Comprehensive test suite before refactoring |
| Import path changes | Use automated refactoring tools (rope, bowler) |
| Lost functionality | Code review + integration testing |
| Performance regression | Benchmark before/after |

## 📊 Impact

- **Priority:** 🟡 MEDIUM
- **Effort:** 2-3 weeks (spread across files)
- **Risk:** Medium (large changes, but well-tested)
- **Benefit:** Major improvement in code quality

## 🔗 Related Issues

- Part of Phase 2: Technical Debt Reduction
- Related to #TBD (Master Tracking Issue)
- May reveal issues requiring separate fixes

## ✅ Acceptance Criteria

- [ ] No Python files exceed 800 lines
- [ ] Each module has single, clear responsibility
- [ ] All existing tests pass
- [ ] New unit tests added for extracted components
- [ ] Code coverage maintained or improved
- [ ] Documentation updated to reflect new structure
- [ ] No functional regressions

---

**Priority:** MEDIUM | **Phase:** 2 | **Estimated Time:** 2-3 weeks
