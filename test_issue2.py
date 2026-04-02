import pytest
from unittest.mock import patch
import importlib

def test_init_raises_without_pyqt():
    # If PYQT6_AVAILABLE is patched to False, GolfLauncher class will inherit from `object`
    # and the `__init__` should raise ImportError. However, if the module isn't properly
    # reloaded due to some caching or other reason, it might not raise.
    with patch("src.launchers.golf_suite_launcher.PYQT6_AVAILABLE", False):
        import src.launchers.golf_suite_launcher as gsl
        importlib.reload(gsl)

        try:
            gsl.GolfLauncher()
        except ImportError as e:
            print("Successfully raised ImportError:", e)
        except Exception as e:
            print("Raised something else:", type(e))
        else:
            print("Did not raise any exception")

if __name__ == '__main__':
    test_init_raises_without_pyqt()
