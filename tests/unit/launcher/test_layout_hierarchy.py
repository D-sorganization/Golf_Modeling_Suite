"""Regression tests for issue #5624 — launcher visual hierarchy.

Defect A: ``QMenuBar`` renders ABOVE the ``CustomTitleBar`` because
``init_ui`` calls ``self.setMenuBar(...)`` — a native ``QMainWindow``
API that places the menu bar above the central widget where the
title bar lives.

These tests pin the contract that the frameless launcher must layer
its chrome in the order:

    1. ``CustomTitleBar``   (black, top)
    2. ``QMenuBar``         (gray, File/View/Tools/Help)
    3. main horizontal splitter (sidebar | content | sidekick)

Design: TDD/DbC/LOD/DRY.

* TDD — these tests are written RED-first against current ``init_ui``.
* DbC — the launcher exposes a contract that ``outer_vbox`` always
  contains, in order, ``self.title_bar`` then ``self.menu_bar`` then
  the splitter; ``QMainWindow.setMenuBar`` is never called.
* LOD — tests reach only into ``centralWidget().layout()`` and the
  publicly assigned ``self.title_bar`` / ``self.menu_bar``.
* DRY — shared launcher fixture in this module-private factory.
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import (
    QApplication,
    QMenuBar,
    QSplitter,
    QVBoxLayout,
)

from src.launchers.custom_title_bar import CustomTitleBar


pytestmark = pytest.mark.ui


# ---------------------------------------------------------------------------
# Shared launcher fixture (DRY) — a stripped-down mixin-only instance.
# ---------------------------------------------------------------------------


@pytest.fixture
def ui_setup(qapp):
    """Construct just enough of the launcher to call ``init_ui``.

    The full ``GolfLauncher`` pulls in async startup workers, Docker
    probes, and a worker thread pool that we do not need here.  We
    mount the UI-setup mixin on a bare ``QMainWindow`` subclass that
    provides the handful of attribute/method stubs ``init_ui`` reads
    from its co-mixins.
    """
    from PyQt6.QtWidgets import QMainWindow

    from src.launchers.launcher_ui_setup import LauncherUISetupMixin

    class _DummyLayoutManager:
        tile_scale = 0.75

        def set_view_mode(self, *_a, **_k) -> None: ...
        def set_tile_scale(self, *_a, **_k) -> None: ...
        def rebuild_grid(self, *_a, **_k) -> None: ...

    # Import the production ``_install_sidekick_sidebar`` so we can bind
    # it to the harness — the install method lives on ``GolfLauncher``
    # itself, not on the UI mixin, but the layout integration that
    # #5624 fixes is the same regardless of caller.
    from src.launchers.golf_launcher import GolfLauncher as _RealLauncher

    class _UIHarness(LauncherUISetupMixin, QMainWindow):  # type: ignore[misc]
        # Re-use the production install method so #5624 tests exercise
        # the real code path.
        _install_sidekick_sidebar = _RealLauncher._install_sidekick_sidebar

        def __init__(self) -> None:
            super().__init__()
            self.layout_manager = _DummyLayoutManager()
            self.docker_available = False

        # The grid uses these on _on_view_mode_changed; safe no-ops.
        def _show_preferences(self, *_a, **_k) -> None: ...
        def _toggle_layout_mode_from_menu(self, *_a, **_k) -> None: ...
        def _toggle_context_help(self, *_a, **_k) -> None: ...
        def _show_help_dialog(self, *_a, **_k) -> None: ...
        def _show_shortcuts_overlay(self, *_a, **_k) -> None: ...
        def _show_about_dialog(self, *_a, **_k) -> None: ...
        def _open_project_map(self, *_a, **_k) -> None: ...
        def _open_settings(self, *_a, **_k) -> None: ...
        def _show_help_dialog_topic(self, *_a, **_k) -> None: ...
        def _on_docker_mode_changed(self, *_a, **_k) -> None: ...
        def _on_wsl_mode_changed(self, *_a, **_k) -> None: ...
        def toggle_layout_mode(self, *_a, **_k) -> None: ...
        def open_layout_manager(self, *_a, **_k) -> None: ...
        def update_search_filter(self, *_a, **_k) -> None: ...
        def launch_simulation(self, *_a, **_k) -> None: ...
        def _setup_theme_menu(self, *_a, **_k) -> None: ...
        def apply_styles(self) -> None: ...

    window = _UIHarness()
    window.init_ui()
    yield window
    window.deleteLater()
    QApplication.processEvents()


def _outer_vbox(window) -> QVBoxLayout:
    central = window.centralWidget()
    layout = central.layout()
    assert isinstance(layout, QVBoxLayout)
    return layout


def _ordered_widgets(layout: QVBoxLayout) -> list:
    widgets = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        w = item.widget() if item is not None else None
        if w is not None:
            widgets.append(w)
    return widgets


# ---------------------------------------------------------------------------
# Defect A — Title bar / menu bar / splitter order
# ---------------------------------------------------------------------------


class TestLayoutHierarchy:
    """The launcher's ``outer_vbox`` must layer chrome in the right order."""

    def test_title_bar_is_first_child_of_outer_vbox(self, ui_setup) -> None:
        widgets = _ordered_widgets(_outer_vbox(ui_setup))
        assert widgets, "outer_vbox must have at least one child widget"
        assert isinstance(widgets[0], CustomTitleBar), (
            f"expected CustomTitleBar first; got {type(widgets[0]).__name__}"
        )

    def test_menu_bar_is_second_child_below_title_bar(self, ui_setup) -> None:
        widgets = _ordered_widgets(_outer_vbox(ui_setup))
        assert len(widgets) >= 2, (
            "outer_vbox must contain title bar, menu bar, and splitter"
        )
        assert isinstance(widgets[1], QMenuBar), (
            f"expected QMenuBar second; got {type(widgets[1]).__name__}"
        )

    def test_setmenubar_is_not_called_in_frameless_mode(self, ui_setup) -> None:
        """``QMainWindow.setMenuBar`` reserves the native top strip.

        On a frameless main window that strip sits above the central
        widget — i.e. above the custom title bar — which is exactly
        the regression in #5624.  Contract: after ``init_ui`` the
        populated menu bar is a child of the central widget's layout,
        NOT of the native main-window menu strip.
        """
        native_menu_bar = ui_setup.menuBar()
        # The native menu bar should be empty (no File/View/Tools/Help
        # actions); our menu bar lives in the central widget.
        assert native_menu_bar.actions() == [] or all(
            a.isSeparator() for a in native_menu_bar.actions()
        ), (
            "QMainWindow.setMenuBar was used — populated menu bar found on "
            "native main-window strip; this places it above the title bar"
        )
        # And the menu bar attribute must point to a widget that lives in
        # the central layout, not on the main window directly.
        assert hasattr(ui_setup, "menu_bar"), (
            "init_ui must expose self.menu_bar as a QMenuBar in outer_vbox"
        )
        widgets = _ordered_widgets(_outer_vbox(ui_setup))
        assert ui_setup.menu_bar in widgets, (
            "self.menu_bar must be a direct child of outer_vbox"
        )

    def test_splitter_comes_after_menu_bar(self, ui_setup) -> None:
        widgets = _ordered_widgets(_outer_vbox(ui_setup))
        # Find indices of the title bar and the splitter.
        splitter_indices = [
            i for i, w in enumerate(widgets) if isinstance(w, QSplitter)
        ]
        menubar_indices = [
            i for i, w in enumerate(widgets) if isinstance(w, QMenuBar)
        ]
        assert splitter_indices, "expected at least one QSplitter in outer_vbox"
        assert menubar_indices, "expected a QMenuBar in outer_vbox"
        assert min(splitter_indices) > max(menubar_indices), (
            "the main QSplitter must come below the menu bar"
        )
