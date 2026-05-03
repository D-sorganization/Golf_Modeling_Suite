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

"""Tests for upstream_drift_tools.ui.catppuccin_theme (Issues #1949, #1744)."""


from src.shared.python.upstream_drift_tools.ui.catppuccin_theme import (
    COLORS,
    get_stylesheet,
)


class TestCatppuccinColors:
    def test_colors_is_dict(self) -> None:
        assert isinstance(COLORS, dict)

    def test_colors_not_empty(self) -> None:
        assert len(COLORS) > 0

    def test_has_base_color(self) -> None:
        assert "base" in COLORS

    def test_has_text_color(self) -> None:
        assert "text" in COLORS


class TestGetStylesheet:
    def test_returns_string(self) -> None:
        ss = get_stylesheet()
        assert isinstance(ss, str)

    def test_stylesheet_not_empty(self) -> None:
        ss = get_stylesheet()
        assert len(ss) > 0

    def test_stylesheet_contains_css(self) -> None:
        ss = get_stylesheet()
        assert "{" in ss and "}" in ss
