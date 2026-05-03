import os as _os, sys as _sys

def _should_skip_gui_import() -> bool:
    if _os.environ.get("HEADLESS_CI") == "1":
        return True
    if any("pytest" in _a for _a in _sys.argv) and not _os.environ.get("FORCE_GUI_TESTS"):
        return True
    return False

if _should_skip_gui_import():
    import pytest as _pytest
    _pytest.skip("Skipping GUI tests in headless mode", allow_module_level=True)

import pytest


def test_headless_plotting_import() -> None:
    """Test that plotting_core can be imported without PyQt6.

    Note: The plotting_core module was removed from the codebase.
    This test is skipped because the module no longer exists.
    """
    pytest.skip(
        "src.shared.python.plotting_core was removed; "
        "plotting functionality has been reorganized"
    )
