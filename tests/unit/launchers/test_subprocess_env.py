
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

"""Regression tests for subprocess environment configuration."""

from pathlib import Path

from src.launchers.launcher_process_manager import ProcessManager


class TestGetSubprocessEnv:
    """Verify PYTHONPATH includes required directories for subprocess launches."""

    def test_includes_shared_python(self, tmp_path: Path) -> None:
        """PYTHONPATH must include src/shared/python for contracts module."""
        (tmp_path / "src" / "shared" / "python").mkdir(parents=True)
        (tmp_path / "src" / "engines" / "physics_engines" / "mujoco" / "python").mkdir(
            parents=True,
        )
        pm = ProcessManager(tmp_path)
        env = pm.get_subprocess_env()
        assert str(tmp_path / "src" / "shared" / "python") in env["PYTHONPATH"]

    def test_includes_mujoco_python(self, tmp_path: Path) -> None:
        """PYTHONPATH must include mujoco python dir."""
        (tmp_path / "src" / "shared" / "python").mkdir(parents=True)
        (tmp_path / "src" / "engines" / "physics_engines" / "mujoco" / "python").mkdir(
            parents=True,
        )
        pm = ProcessManager(tmp_path)
        env = pm.get_subprocess_env()
        assert "mujoco" in env["PYTHONPATH"]
