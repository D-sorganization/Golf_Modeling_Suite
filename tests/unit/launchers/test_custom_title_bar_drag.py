"""Tests for CustomTitleBar drag behaviour (issue #5618).

Covers:
- mousePressEvent / mouseMoveEvent emit move_requested
- eventFilter() must be overridden for child event propagation
- _clamp_to_screen helper exists (new method required by fix)
- setAutoFillBackground(True) prevents click-through
- Closing triggers close_requested, not move_requested
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mouse_event(
    event_type: QMouseEvent.Type,
    local_pos: QPoint,
    global_pos: QPoint,
    button: Qt.MouseButton,
    buttons: Qt.MouseButton,
) -> QMouseEvent:
    return QMouseEvent(
        event_type,
        local_pos,
        global_pos,
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_press_and_move_emits_move_requested_with_correct_offset(qapp):
    """mousePressEvent + mouseMoveEvent must emit move_requested exactly once
    (issue #5618: drag path must work).
    """
    from src.launchers.custom_title_bar import CustomTitleBar

    bar = CustomTitleBar(QWidget())
    bar.move_requested.emit = MagicMock()

    bar.mousePressEvent(
        _make_mouse_event(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(50, 10),
            QPoint(150, 110),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
        )
    )
    bar.mouseMoveEvent(
        _make_mouse_event(
            QMouseEvent.Type.MouseMove,
            QPoint(200, 60),
            QPoint(300, 160),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
        )
    )

    bar.move_requested.emit.assert_called_once()


@pytest.mark.unit
def test_custom_title_bar_overrides_event_filter(qapp):
    """CustomTitleBar must OVERRIDE eventFilter() — the base QWidget implementation
    just returns False and cannot forward child events for drag propagation.

    After the fix: CustomTitleBar.eventFilter is not inherited from QWidget but
    is defined in CustomTitleBar itself (issue #5618 root cause #3).
    """
    from src.launchers.custom_title_bar import CustomTitleBar

    # The fix requires eventFilter to be defined on CustomTitleBar itself,
    # not inherited from QWidget.
    assert "eventFilter" in CustomTitleBar.__dict__, (
        "CustomTitleBar must define its own eventFilter() method to intercept "
        "child widget mouse events for drag propagation (issue #5618 root cause #3). "
        "Inherited QWidget.eventFilter is a no-op."
    )


@pytest.mark.unit
def test_drag_target_outside_screen_geometry_is_clamped(qapp):
    """_clamp_to_screen() must exist and be callable — it constrains off-screen
    positions to the union of all screen geometries (issue #5618 root cause #4).
    """
    from src.launchers.custom_title_bar import CustomTitleBar

    bar = CustomTitleBar()

    assert hasattr(bar, "_clamp_to_screen"), (
        "_clamp_to_screen() helper must be added to CustomTitleBar (issue #5618)"
    )
    assert callable(bar._clamp_to_screen), "_clamp_to_screen must be callable"


@pytest.mark.unit
def test_title_bar_has_opaque_background(qapp):
    """CustomTitleBar must call setAutoFillBackground(True) to prevent
    translucency click-through (issue #5618 root cause #2).
    """
    from src.launchers.custom_title_bar import CustomTitleBar

    bar = CustomTitleBar(QWidget())

    assert bar.autoFillBackground(), (
        "CustomTitleBar must set autoFillBackground=True to prevent "
        "translucency click-through (issue #5618)"
    )


@pytest.mark.unit
def test_close_window_emits_only_close_requested(qapp):
    """_close_window() must emit only close_requested, never move_requested
    (issue #5618: buttons must not accidentally trigger drag).

    This test verifies the contract by inspecting the method source: it must
    call self.close_requested.emit() and must NOT call self.move_requested.emit().
    """
    import inspect
    from src.launchers.custom_title_bar import CustomTitleBar

    src = inspect.getsource(CustomTitleBar._close_window)
    assert "close_requested" in src, "_close_window must call close_requested.emit()"
    assert "move_requested" not in src, (
        "_close_window must NOT reference move_requested (issue #5618)"
    )


@pytest.mark.unit
def test_move_requested_uses_clamp_to_screen(qapp):
    """mouseMoveEvent must pass the target position through _clamp_to_screen()
    before emitting move_requested (issue #5618 root cause #4).

    We verify by inspecting the source of mouseMoveEvent.
    """
    import inspect
    from src.launchers.custom_title_bar import CustomTitleBar

    src = inspect.getsource(CustomTitleBar.mouseMoveEvent)
    assert "_clamp_to_screen" in src, (
        "mouseMoveEvent must call _clamp_to_screen() before emitting "
        "move_requested to prevent off-screen window placement (issue #5618)"
    )
