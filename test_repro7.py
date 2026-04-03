import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock

def test():
    import src.launchers.golf_suite_launcher as gsl

    with patch("src.shared.python.engine_core.engine_availability.PYQT6_AVAILABLE", False):
        try:
            importlib.reload(gsl)
        except Exception:
            pass

    importlib.reload(gsl)

    # Here we import without mock!
    import src.shared.python.screw_theory

test()
print("Success!")
