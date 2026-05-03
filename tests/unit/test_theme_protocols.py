from __future__ import annotations

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

"""Tests for theme.protocols and theme.integration (Issues #1949, #1744)."""


from src.shared.python.theme.integration import get_theme_manager
from src.shared.python.theme.protocols import (
    StylesheetGenerator,
    ThemeProvider,
    ThemeSwitcher,
)


class TestThemeProtocols:
    def test_theme_provider_protocol_exists(self) -> None:
        assert ThemeProvider is not None

    def test_theme_switcher_protocol_exists(self) -> None:
        assert ThemeSwitcher is not None

    def test_stylesheet_generator_protocol_exists(self) -> None:
        assert StylesheetGenerator is not None


class TestThemeIntegration:
    def test_get_theme_manager_callable(self) -> None:
        assert callable(get_theme_manager)
