
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

import pytest
from double_pendulum_model.ui.pendulum_pyqt_app import PendulumController
from PyQt6.QtWidgets import QApplication


def test_smoke() -> None:
    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(["test", "-platform", "offscreen"])

    try:
        window = PendulumController()
        assert window is not None
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"Could not instantiate PendulumController: {e}")
