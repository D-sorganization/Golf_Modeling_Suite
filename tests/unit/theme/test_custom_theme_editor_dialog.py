"""Smoke test for ``CustomThemeEditor`` (PR #5406, issue #5487).

The dialog itself was added in 475 lines of code without any targeted
tests. We exercise the end-to-end Save path: instantiate the dialog,
inject a colour through the public ``_on_color_changed`` slot, click the
``Save`` button, and assert that ``ThemeManager.save_custom_theme`` was
called with the expected arguments.

The test is gated on real PyQt6 + ``pytest-qt`` being available; the
parent ``conftest.py`` autouse fixture skips the module otherwise.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.shared.python.theme.colors import THEME_COLOR_KEYS
from src.shared.python.theme.theme_manager import ThemeManager


pytest.importorskip("pytestqt", reason="pytest-qt required for dialog smoke test")


def _make_palette() -> dict[str, str]:
    """Return a fully populated valid palette (mirrors make_theme_dict)."""
    palette = [
        "#101820",
        "#1f2933",
        "#3e4c59",
        "#e4e7eb",
        "#cbd2d9",
        "#9aa5b1",
        "#52606d",
        "#0b0e13",
        "#f0b429",
        "#2d3742",
        "#f0b429",
        "#1f2933",
        "#323f4b",
        "#f7c948",
    ]
    return dict(zip(THEME_COLOR_KEYS, palette, strict=True))


def test_dialog_save_calls_theme_manager_save_custom_theme(
    qtbot, isolated_qsettings: Path
) -> None:
    """End-to-end: type a name, simulate colour picks, click Save."""
    del isolated_qsettings  # used for the QSettings isolation side-effect

    from src.shared.python.theme.dialogs.custom_theme_editor import (
        CustomThemeEditor,
    )

    ThemeManager.reset_instance()
    manager = ThemeManager()

    dialog = CustomThemeEditor(manager)
    qtbot.addWidget(dialog)

    # Type the theme name.
    dialog.name_edit.setText("DialogSmokeTheme")

    # Simulate the user picking every colour via the public slot the
    # ColorPickerButton invokes when its picker closes.
    palette = _make_palette()
    for key, value in palette.items():
        dialog._on_color_changed(key, value)  # noqa: SLF001

    # Spy on the manager call rather than running the real persistence
    # round trip a second time -- the round trip is covered in
    # ``test_custom_theme.py``.
    with (
        patch.object(
            manager,
            "save_custom_theme",
            wraps=manager.save_custom_theme,
        ) as spy,
        patch(
            "src.shared.python.theme.dialogs.custom_theme_editor.QMessageBox"
        ) as mock_msgbox,
    ):
        mock_msgbox.warning = MagicMock()
        mock_msgbox.information = MagicMock()
        mock_msgbox.critical = MagicMock()

        ok = dialog._perform_save(apply_immediately=False)  # noqa: SLF001

    assert ok is True, "Save should report success"
    spy.assert_called_once()

    args, kwargs = spy.call_args
    # The dialog passes (name, colors, apply_immediately) positionally.
    assert args[0] == "DialogSmokeTheme"
    saved_colors = args[1]
    apply_flag = args[2] if len(args) > 2 else kwargs.get("apply_immediately")
    assert apply_flag is False

    # Colours posted to the manager match what we injected.
    for key, value in palette.items():
        assert saved_colors[key] == value

    # And the manager wrote it through to its registry.
    assert "DialogSmokeTheme" in manager.get_custom_theme_names()


def test_dialog_blocks_save_with_builtin_name(qtbot, isolated_qsettings: Path) -> None:
    """Dialog must refuse to save with a built-in theme name."""
    del isolated_qsettings

    from src.shared.python.theme.dialogs.custom_theme_editor import (
        CustomThemeEditor,
    )

    ThemeManager.reset_instance()
    manager = ThemeManager()

    dialog = CustomThemeEditor(manager)
    qtbot.addWidget(dialog)

    dialog.name_edit.setText("Light")  # built-in
    for key, value in _make_palette().items():
        dialog._on_color_changed(key, value)  # noqa: SLF001

    with (
        patch.object(manager, "save_custom_theme") as spy,
        patch("src.shared.python.theme.dialogs.custom_theme_editor.QMessageBox"),
    ):
        ok = dialog._perform_save(apply_immediately=False)  # noqa: SLF001

    assert ok is False
    spy.assert_not_called()
    assert "Light" not in manager.get_custom_theme_names()
