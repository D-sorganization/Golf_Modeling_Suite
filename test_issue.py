import pytest
from unittest.mock import patch
import importlib

def test_init_raises_without_pyqt():
    with patch("src.launchers.golf_suite_launcher.PYQT6_AVAILABLE", False):
        import src.launchers.golf_suite_launcher as gsl

        importlib.reload(gsl)

        with pytest.raises(ImportError, match="PyQt6 is required"):
            gsl.GolfLauncher()
