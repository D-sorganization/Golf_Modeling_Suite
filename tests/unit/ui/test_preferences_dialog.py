"""Headless smoke test for the launcher Preferences dialog (#4491)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6.QtWidgets")


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    a = QApplication.instance() or QApplication([])
    yield a


def test_preferences_dialog_opens_without_attribute_error(app):
    from src.shared.python.ui.preferences_dialog import PreferencesDialog

    dlg = PreferencesDialog(parent=None)
    # appearance tab built without crash
    assert dlg.theme_combo.count() >= 3, "expected at least Dark/Light/HighContrast"
    # The bug was in the appearance-tab path; just instantiating proves the fix.
