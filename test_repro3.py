import sys
import importlib
import pytest
from unittest.mock import patch

def test():
    # First mock PyQt6 so it doesn't fail import when we restore
    import sys
    sys.modules['PyQt6'] = type('Mock', (), {})
    sys.modules['PyQt6.QtCore'] = type('Mock', (), {})
    sys.modules['PyQt6.QtWidgets'] = type('Mock', (), {})
    sys.modules['PyQt6.QtGui'] = type('Mock', (), {})

    import src.launchers.golf_suite_launcher as gsl
    with patch("src.shared.python.engine_core.engine_availability.PYQT6_AVAILABLE", False):
        importlib.reload(gsl)

        # What happens to the namespace package?
        print("engines" in sys.modules)
        print("engines.physics_engines" in sys.modules)

    importlib.reload(gsl)

    # Try importing something from pinocchio screw kinematics
    from src.engines.physics_engines.pinocchio.python.pinocchio_screw_kinematics import ScrewKinematicsAnalyzer

test()
print("Success!")
