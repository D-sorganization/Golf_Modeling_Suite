
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

from double_pendulum_model.ui.pendulum_pyqt_app import PendulumController
from PyQt6.QtWidgets import QApplication


def test_tooltips() -> None:
    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(["test", "-platform", "offscreen"])

    window = PendulumController()

    # Check button tooltips
    assert window.start_button.toolTip() == "Start the simulation"
    assert window.stop_button.toolTip() == "Pause the simulation"
    assert window.reset_button.toolTip() == "Reset simulation to initial state"

    # Check input tooltips
    for entry in window.torque_inputs.values():
        assert "Constant value" in entry.toolTip()

    for entry in window.velocity_inputs.values():
        assert "Polynomial coefficients" in entry.toolTip()
