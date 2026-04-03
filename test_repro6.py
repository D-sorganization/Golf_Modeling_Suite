import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock

def test():
    # Setup mock PyQt6
    pyqt6 = MagicMock()
    sys.modules['PyQt6'] = pyqt6
    sys.modules['PyQt6.QtCore'] = pyqt6.QtCore
    sys.modules['PyQt6.QtGui'] = pyqt6.QtGui
    sys.modules['PyQt6.QtWidgets'] = pyqt6.QtWidgets

    import src.launchers.golf_suite_launcher as gsl

    with patch("src.shared.python.engine_core.engine_availability.PYQT6_AVAILABLE", False):
        try:
            importlib.reload(gsl)
        except Exception:
            pass

    # Here we import without mock!
    import src.shared.python.screw_theory

test()
print("Success!")
