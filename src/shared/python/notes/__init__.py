"""Shared notes workspace package.

Provides a reusable project-backed notes file model with safe deletion
(recycle bin) and a PyQt dock widget that can be embedded or popped out.
"""

from __future__ import annotations

from .models import RecycledNoteItem
from .storage import NotesStorage

import os
import sys

def _should_skip_gui_import() -> bool:
    if os.environ.get("HEADLESS_CI") == "1":
        return True
    if any("pytest" in arg for arg in sys.argv) and not os.environ.get("FORCE_GUI_TESTS"):
        return True
    return False

if _should_skip_gui_import():
    _PYQT6_AVAILABLE = False
    class NotesDockWidget:  # type: ignore[no-redef]
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise ImportError("PyQt6 is required for NotesDockWidget")
else:
    try:
        from .notes_dock_widget import NotesDockWidget
        _PYQT6_AVAILABLE = True
    except ImportError:
        _PYQT6_AVAILABLE = False

        class NotesDockWidget:  # type: ignore[no-redef]
            """Fallback placeholder when PyQt6 is unavailable."""

            def __init__(self, *_args: object, **_kwargs: object) -> None:
                raise ImportError("PyQt6 is required for NotesDockWidget")


__all__ = [
    "NotesStorage",
    "RecycledNoteItem",
    "NotesDockWidget",
]
