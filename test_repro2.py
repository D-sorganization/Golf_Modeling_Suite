import sys
import importlib
import pytest
from unittest.mock import patch

def test():
    import src.launchers.golf_suite_launcher as gsl
    with patch("src.shared.python.engine_core.engine_availability.PYQT6_AVAILABLE", False):
        importlib.reload(gsl)
    importlib.reload(gsl)

    # Try importing something from pinocchio screw kinematics
    from src.engines.physics_engines.pinocchio.python.pinocchio_screw_kinematics import ScrewKinematicsAnalyzer

test()
print("Success!")
