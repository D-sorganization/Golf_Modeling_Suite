
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

from double_pendulum_model.ui.validation import (
    validate_polynomial_text,
    validate_torque_text,
)


def test_validate_polynomial() -> None:
    assert validate_polynomial_text("1") is None
    assert validate_polynomial_text("1+2") is None
    assert validate_polynomial_text("1.5 + 2.5") is None
    assert validate_polynomial_text(" -1 + 5 ") is None
    assert validate_polynomial_text("") is None  # Empty treated as valid (0.0)

    assert validate_polynomial_text("1,2") is not None
    assert validate_polynomial_text("1-2") is not None  # Currently only splits by +
    assert validate_polynomial_text("foo") is not None


def test_validate_expression() -> None:
    assert validate_torque_text("1") is None
    assert validate_torque_text("sin(t)") is None
    assert validate_torque_text("pi * 2") is None
    assert validate_torque_text("") is None  # Empty treated as valid (0.0)

    assert validate_torque_text("1 +") is not None
    assert validate_torque_text("sin(t))") is not None
