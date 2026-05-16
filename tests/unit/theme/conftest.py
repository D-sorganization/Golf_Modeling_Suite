"""Shared fixtures for theme manager + theme dialog tests.

The repo-wide ``tests/conftest.py`` mocks ``PyQt6`` on platforms where the
real DLLs cannot be loaded. ``ThemeManager`` inherits from ``QObject`` and
calls ``QSettings`` / ``QStandardPaths`` at construction time, so the mock
breaks instantiation. This conftest swaps the mock for the real Qt
implementation when PyQt6 is actually installed, and skips the suite
otherwise.

It also redirects ``QStandardPaths`` to its test directory and gives each
``ThemeManager`` instance a unique ``QSettings`` organisation so saved
custom themes never bleed into a developer's real Qt config.
"""

from __future__ import annotations

import importlib
import os
import sys
import uuid
from pathlib import Path

import pytest

# Headless-safe defaults must be set before any Qt import.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTEST_QT_API", "pyqt6")


def _ensure_real_pyqt6() -> bool:
    """Swap the root-conftest PyQt6 MagicMock for the real package.

    Returns True if real PyQt6 is now loaded, False if the import failed
    (in which case the calling tests should skip).
    """
    # Drop any mocks the parent conftest installed.
    for module_name in list(sys.modules):
        if module_name == "PyQt6" or module_name.startswith("PyQt6."):
            module = sys.modules[module_name]
            module_repr = repr(type(module))
            if "Mock" in module_repr:
                del sys.modules[module_name]

    try:
        importlib.import_module("PyQt6.QtCore")
        importlib.import_module("PyQt6.QtWidgets")
        importlib.import_module("PyQt6.QtGui")
    except (ImportError, ModuleNotFoundError):
        return False

    # Sanity check: ensure ``QObject`` is a real class, not a Mock.
    from PyQt6.QtCore import QObject

    return isinstance(QObject, type)


_REAL_PYQT6_AVAILABLE = _ensure_real_pyqt6()


@pytest.fixture(autouse=True)
def _require_real_pyqt6() -> None:
    """Skip the theme test bucket when PyQt6 cannot be loaded for real."""
    if not _REAL_PYQT6_AVAILABLE:
        pytest.skip("Real PyQt6 is required for ThemeManager tests")


@pytest.fixture
def isolated_qsettings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect QSettings + QStandardPaths to a per-test temp directory.

    Each test gets a unique QSettings organisation so custom themes saved
    in one test cannot be observed by another. ``QStandardPaths`` is told
    to use a test directory inside ``tmp_path`` so the JSON persistence
    file lives there too.
    """
    from PyQt6.QtCore import QCoreApplication, QSettings, QStandardPaths

    # Force ini-format settings into ``tmp_path`` so we never touch the
    # developer's real registry/AppData entries.
    settings_path = tmp_path / "qsettings"
    settings_path.mkdir(exist_ok=True)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(settings_path),
    )

    # Redirect ``QStandardPaths`` writable locations into ``tmp_path``.
    # Setting ``XDG_CONFIG_HOME`` works on Linux; on Windows/macOS Qt
    # ignores it and we additionally enable test mode so the path falls
    # under a ``qttest`` subfolder we can verify lives outside production.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    QStandardPaths.setTestModeEnabled(True)

    # Unique organisation per test so QSettings cannot collide.
    org = f"UpstreamDriftTest-{uuid.uuid4().hex[:12]}"
    app = "ThemeManagerTests"
    QCoreApplication.setOrganizationName(org)
    QCoreApplication.setApplicationName(app)

    yield tmp_path

    QStandardPaths.setTestModeEnabled(False)
