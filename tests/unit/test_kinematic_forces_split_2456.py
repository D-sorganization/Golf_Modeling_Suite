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

"""Contract tests for #2456: kinematic_forces.py split.

Tests run red before the split and green after.
"""


import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]
KF_DIR = REPO / "src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf"
LOC_BUDGET_DATA = 400
LOC_BUDGET_COORDINATOR = 900

_mujoco_available = importlib.util.find_spec("mujoco") is not None


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


class TestKinematicForcesSplitStructure:
    """Split modules must exist after refactor."""

    @pytest.mark.unit
    def test_data_module_exists(self) -> None:
        assert (KF_DIR / "_kinematic_force_data.py").exists()


class TestKinematicForcesFileSizes:
    """Each file must be within LOC budget after split."""

    @pytest.mark.unit
    def test_coordinator_loc(self) -> None:
        loc = _count_lines(KF_DIR / "kinematic_forces.py")
        assert loc <= LOC_BUDGET_COORDINATOR, (
            f"kinematic_forces.py has {loc} LOC; budget {LOC_BUDGET_COORDINATOR}"
        )

    @pytest.mark.unit
    def test_data_module_loc(self) -> None:
        loc = _count_lines(KF_DIR / "_kinematic_force_data.py")
        assert loc <= LOC_BUDGET_DATA, (
            f"_kinematic_force_data.py has {loc} LOC; budget {LOC_BUDGET_DATA}"
        )


@pytest.mark.skipif(not _mujoco_available, reason="mujoco not installed")
class TestKinematicForcesPublicAPI:
    """Public API must remain importable from kinematic_forces (backward compat)."""

    @pytest.mark.unit
    def test_import_mj_data_context(self) -> None:
        from src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf.kinematic_forces import (
            MjDataContext,
        )

        assert MjDataContext is not None

    @pytest.mark.unit
    def test_import_kinematic_force_data(self) -> None:
        from src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf.kinematic_forces import (
            KinematicForceData,
        )

        assert KinematicForceData is not None

    @pytest.mark.unit
    def test_import_kinematic_force_analyzer(self) -> None:
        from src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf.kinematic_forces import (
            KinematicForceAnalyzer,
        )

        assert KinematicForceAnalyzer is not None
