from __future__ import annotations

import os
import sys

def _should_skip_gui_import() -> bool:
    if os.environ.get("HEADLESS_CI") == "1":
        return True
    if any("pytest" in arg for arg in sys.argv) and not os.environ.get("FORCE_GUI_TESTS"):
        return True
    return False

if _should_skip_gui_import():
    import pytest
    pytest.skip("Skipping GUI tests in headless mode", allow_module_level=True)

"""Contract tests for #2456: grip_modelling_tab.py split.

Tests run red before the split and green after.
"""


import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]
GRIP_DIR = REPO / "src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf"
LOC_BUDGET_WIDGETS = 400
LOC_BUDGET_COORDINATOR = 900

_mujoco_available = importlib.util.find_spec("mujoco") is not None


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


class TestGripModellingSplitStructure:
    """Split modules must exist after refactor."""

    @pytest.mark.unit
    def test_widgets_module_exists(self) -> None:
        assert (GRIP_DIR / "_grip_modelling_widgets.py").exists()


class TestGripModellingFileSizes:
    """Each file must be within LOC budget after split."""

    @pytest.mark.unit
    def test_coordinator_loc(self) -> None:
        loc = _count_lines(GRIP_DIR / "grip_modelling_tab.py")
        assert loc <= LOC_BUDGET_COORDINATOR, (
            f"grip_modelling_tab.py has {loc} LOC; budget {LOC_BUDGET_COORDINATOR}"
        )

    @pytest.mark.unit
    def test_widgets_loc(self) -> None:
        loc = _count_lines(GRIP_DIR / "_grip_modelling_widgets.py")
        assert loc <= LOC_BUDGET_WIDGETS, (
            f"_grip_modelling_widgets.py has {loc} LOC; budget {LOC_BUDGET_WIDGETS}"
        )


@pytest.mark.skipif(not _mujoco_available, reason="mujoco not installed")
class TestGripModellingPublicAPI:
    """Public API must remain importable from grip_modelling_tab (backward compat)."""

    @pytest.mark.unit
    def test_import_pressure_visualization_widget(self) -> None:
        from src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf.grip_modelling_tab import (
            PressureVisualizationWidget,
        )

        assert PressureVisualizationWidget is not None

    @pytest.mark.unit
    def test_import_contact_metrics_widget(self) -> None:
        from src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf.grip_modelling_tab import (
            ContactMetricsWidget,
        )

        assert ContactMetricsWidget is not None

    @pytest.mark.unit
    def test_import_grip_modelling_tab(self) -> None:
        from src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf.grip_modelling_tab import (
            GripModellingTab,
        )

        assert GripModellingTab is not None
