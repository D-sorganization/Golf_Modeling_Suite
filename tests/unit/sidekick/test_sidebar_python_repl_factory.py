"""Tests for the sidebar python-repl tab factory (Issue #5649).

TDD: written before the fix.  Asserts that the factory registered for the
'python-repl' tab uses PythonReplWidget rather than a QLabel placeholder.

Prior to the fix, _make_python_repl_widget returned self._placeholder(...)
which is a QLabel — a non-interactive placeholder that gives users no REPL.
"""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Detect real PyQt6 vs conftest mock — mirrors test_python_repl_widget.py
# ---------------------------------------------------------------------------
_pyqt6_module = sys.modules.get("PyQt6")
try:
    _qtcore = getattr(_pyqt6_module, "QtCore", None)
    _qabt = getattr(_qtcore, "QAbstractTableModel", None)
    _HAVE_REAL_QT = (
        _qabt is not None
        and isinstance(_qabt, type)
        and not getattr(_qabt, "_mock_name", None)
    )
except Exception:
    _HAVE_REAL_QT = False

_skip_qt = pytest.mark.skipif(
    not _HAVE_REAL_QT,
    reason="PyQt6 not available or mocked by conftest",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sidebar_no_qt() -> Any:
    """Construct UnifiedToolsSidebar bypassing QWidget.__init__."""
    from src.shared.python.upstream_drift_tools.ui.tools_sidebar.sidebar import (
        UnifiedToolsSidebar,
    )
    from src.shared.python.upstream_drift_tools.ui.tools_sidebar.registry import (
        WorkspaceRegistry,
    )

    sidebar = UnifiedToolsSidebar.__new__(UnifiedToolsSidebar)
    sidebar.registry = WorkspaceRegistry()
    sidebar._tab_definitions = sidebar._default_tab_definitions()
    sidebar._active_widgets = {}
    sidebar._parent = None
    return sidebar


# ---------------------------------------------------------------------------
# Tests that run in all environments (no Qt required)
# ---------------------------------------------------------------------------


def test_python_repl_tab_definition_exists() -> None:
    """The 'python-repl' tab must be registered in the default tab definitions."""
    sidebar = _make_sidebar_no_qt()
    tab_ids = [t.tab_id for t in sidebar._tab_definitions]
    assert "python-repl" in tab_ids, f"'python-repl' not found in tab ids: {tab_ids}"


def test_python_repl_tab_has_label() -> None:
    """The 'python-repl' tab must have a non-empty human-readable label."""
    sidebar = _make_sidebar_no_qt()
    definition = next(
        (t for t in sidebar._tab_definitions if t.tab_id == "python-repl"),
        None,
    )
    assert definition is not None
    assert definition.label, "python-repl tab must have a non-empty label"


def test_python_repl_factory_calls_python_repl_widget() -> None:
    """_make_python_repl_widget must attempt to construct PythonReplWidget.

    This is the core regression test for issue #5649.  We mock PythonReplWidget
    so the test runs headlessly, and assert it was called instead of falling
    through directly to _placeholder().
    """
    sidebar = _make_sidebar_no_qt()
    definition = next(
        (t for t in sidebar._tab_definitions if t.tab_id == "python-repl"),
        None,
    )
    assert definition is not None, "python-repl tab definition not found"

    fake_widget = MagicMock()
    fake_widget.widget = MagicMock()  # non-None so the branch is taken

    # PythonReplWidget is lazily imported inside _make_python_repl_widget via
    # `from .python_repl import PythonReplWidget`.  Patch the source module.
    repl_module = (
        "src.shared.python.upstream_drift_tools"
        ".ui.tools_sidebar.python_repl.PythonReplWidget"
    )
    # Also patch _placeholder to detect if the factory falls back to it.
    placeholder_called: list[bool] = []

    original_placeholder = sidebar._placeholder

    def _spy_placeholder(label: str) -> Any:
        placeholder_called.append(True)
        return original_placeholder(label)

    sidebar._placeholder = _spy_placeholder  # type: ignore[method-assign]

    with patch(repl_module, return_value=fake_widget) as mock_cls:
        result = definition.factory(sidebar)

    (
        mock_cls.assert_called_once(),
        ("PythonReplWidget constructor was not called — factory did not use it"),
    )
    assert not placeholder_called, (
        "factory fell back to _placeholder instead of returning PythonReplWidget.widget"
    )
    assert result is fake_widget.widget, (
        f"factory returned {result!r} instead of PythonReplWidget.widget"
    )


# ---------------------------------------------------------------------------
# Qt-dependent verification (real widget shape)
# ---------------------------------------------------------------------------


@_skip_qt
def test_python_repl_factory_returns_non_label_widget() -> None:
    """With real Qt, the factory must not return a QLabel placeholder.

    Regression test for issue #5649: after PR #5639 merged, the factory
    returned self._placeholder("Python REPL") which is a QLabel.
    """
    from PyQt6.QtWidgets import QApplication, QLabel, QWidget

    QApplication.instance() or QApplication([])

    from src.shared.python.upstream_drift_tools.ui.tools_sidebar.sidebar import (
        UnifiedToolsSidebar,
    )

    sidebar = UnifiedToolsSidebar(parent=None)
    definition = next(
        (t for t in sidebar._tab_definitions if t.tab_id == "python-repl"),
        None,
    )
    assert definition is not None

    widget = definition.factory(sidebar)

    assert not isinstance(widget, QLabel), (
        f"python-repl factory returned a QLabel placeholder; "
        f"expected a PythonReplWidget-backed QWidget. "
        f"Got: {type(widget).__name__}"
    )
    assert isinstance(widget, QWidget), (
        f"python-repl factory must return a QWidget; got {type(widget).__name__}"
    )
