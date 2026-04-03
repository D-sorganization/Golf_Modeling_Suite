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

    # Try importing something from pinocchio screw kinematics FIRST
    try:
        from src.engines.physics_engines.pinocchio.python import pinocchio_screw_kinematics
    except ImportError:
        pass

    print("Before:", "src.engines.physics_engines" in sys.modules)

    with patch("src.shared.python.engine_core.engine_availability.PYQT6_AVAILABLE", False):
        importlib.reload(gsl)
        print("During:", "src.engines.physics_engines" in sys.modules)

    importlib.reload(gsl)
    print("After:", "src.engines.physics_engines" in sys.modules)

test()
print("Success!")
