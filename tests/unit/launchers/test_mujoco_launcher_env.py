
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

"""Regression tests for MuJoCo launcher subprocess environment.

Ensures PYTHONPATH is correctly set when launching MuJoCo subprocesses,
preventing ModuleNotFoundError for contracts and other shared modules.
"""

import os
from unittest.mock import patch


class TestMujocoLauncherEnv:
    """Test that _get_launch_env produces correct PYTHONPATH."""

    def test_get_launch_env_has_pythonpath(self) -> None:
        from src.launchers.mujoco_unified_launcher import MujocoUnifiedLauncher

        env = MujocoUnifiedLauncher._get_launch_env()
        assert "PYTHONPATH" in env

    def test_get_launch_env_includes_repo_root(self) -> None:
        from src.launchers.mujoco_unified_launcher import (
            REPO_ROOT,
            MujocoUnifiedLauncher,
        )

        env = MujocoUnifiedLauncher._get_launch_env()
        assert str(REPO_ROOT) in env["PYTHONPATH"]

    def test_get_launch_env_includes_src(self) -> None:
        from src.launchers.mujoco_unified_launcher import (
            REPO_ROOT,
            MujocoUnifiedLauncher,
        )

        env = MujocoUnifiedLauncher._get_launch_env()
        assert str(REPO_ROOT / "src") in env["PYTHONPATH"]

    def test_get_launch_env_includes_shared_python(self) -> None:
        from src.launchers.mujoco_unified_launcher import (
            REPO_ROOT,
            MujocoUnifiedLauncher,
        )

        env = MujocoUnifiedLauncher._get_launch_env()
        assert str(REPO_ROOT / "src" / "shared" / "python") in env["PYTHONPATH"]

    def test_get_launch_env_includes_mujoco_python(self) -> None:
        from src.launchers.mujoco_unified_launcher import (
            REPO_ROOT,
            MujocoUnifiedLauncher,
        )

        env = MujocoUnifiedLauncher._get_launch_env()
        mujoco_path = str(
            REPO_ROOT / "src" / "engines" / "physics_engines" / "mujoco" / "python"
        )
        assert mujoco_path in env["PYTHONPATH"]

    def test_get_launch_env_preserves_existing_pythonpath(self) -> None:
        from src.launchers.mujoco_unified_launcher import MujocoUnifiedLauncher

        with patch.dict(os.environ, {"PYTHONPATH": "/custom/path"}):
            env = MujocoUnifiedLauncher._get_launch_env()
            assert "/custom/path" in env["PYTHONPATH"]


class TestSignalToolkitContractsImport:
    """Ensure signal_toolkit can import contracts via absolute path."""

    def test_contracts_require_importable(self) -> None:
        from src.shared.python.contracts import require

        assert callable(require)

    def test_signal_toolkit_core_importable(self) -> None:
        from src.shared.python.signal_toolkit.core import Signal

        assert Signal is not None
