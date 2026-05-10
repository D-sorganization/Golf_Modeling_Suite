"""Chat Quick Bar widget for toolbar integration.

This module provides a compact chat input widget that can be embedded
in any toolbar, with expandable full chat functionality.

Features:
    - Collapsible single-line input in toolbar
    - Keyboard shortcut (Ctrl+Shift+A) to focus
    - Auto-popup on launch (configurable)
    - Expands to full ChatDockWidget on demand
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QEvent, QObject, QShortcut, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QCompleter,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QToolBar,
    QWidget,
    QWidgetAction,
)

from src.shared.python.ai.gui.settings_dialog import get_settings
from src.shared.python.chat import ChatDockWidget

logger = logging.getLogger(__name__)

_DEFAULT_QUICK_PROMPTS = [
    "Help me with...",
    "Explain this code...",
    "Fix this error...",
    "Write a test for...",
    "Optimize this function...",
    "What does this do?",
]


class ChatQuickBar(QWidget):
    """Compact chat input widget for toolbar embedding.

    Provides a single-line input that expands to full chat on demand.

    Signals:
        message_sent: Emitted when a message is sent (content: str)
        chat_expanded: Emitted when the full chat widget is requested
    """

    message_sent = pyqtSignal(str)
    chat_expanded = pyqtSignal()

    def __init__(
        self,
        app_context: str = "default",
        app_name: str = "upstream_drift",
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the quick bar.

        Args:
            app_context: Application context for chat.
            app_name: Application name for session persistence.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._app_context = app_context
        self._app_name = app_name
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        # Input field
        self._input = QLineEdit(self)
        self._input.setPlaceholderText("Ask AI... (Ctrl+Shift+A)")
        self._input.returnPressed.connect(self._on_return_pressed)
        self._input.setFixedWidth(200)

        # Completer for quick prompts
        completer = QCompleter(_DEFAULT_QUICK_PROMPTS, self)
        self._input.setCompleter(completer)

        # Send button
        self._send_btn = QPushButton("Send", self)
        self._send_btn.clicked.connect(self._on_send_clicked)
        self._send_btn.setFixedWidth(50)

        # Expand button
        self._expand_btn = QPushButton("⤢", self)
        self._expand_btn.setToolTip("Expand full chat")
        self._expand_btn.clicked.connect(self.chat_expanded.emit)
        self._expand_btn.setFixedWidth(30)

        layout.addWidget(self._input)
        layout.addWidget(self._send_btn)
        layout.addWidget(self._expand_btn)

        self.setLayout(layout)

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+Shift+A to focus quick bar
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        shortcut.activated.connect(self.focus_input)

    def focus_input(self) -> None:
        """Focus the input field."""
        self._input.setFocus()
        self._input.selectAll()

    def _on_return_pressed(self) -> None:
        """Handle return key press."""
        self._send_message()

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        self._send_message()

    def _send_message(self) -> None:
        """Send the current input as a message."""
        message = self._input.text().strip()
        if message:
            self.message_sent.emit(message)
            self._input.clear()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the quick bar."""
        self._input.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)
        self._expand_btn.setEnabled(enabled)


class ChatLauncherMixin:
    """Mixin for adding chat launcher functionality to QMainWindow.

    Usage:
        class MyApp(ChatLauncherMixin, QMainWindow):
            def __init__(self):
                super().__init__()
                self.init_chat(app_context="gasification", app_name="ips")
    """

    _chat_dock: ChatDockWidget | None = None
    _quick_bar: ChatQuickBar | None = None
    _chat_action: QAction | None = None

    def init_chat(
        self,
        app_context: str,
        app_name: str = "upstream_drift",
        add_to_toolbar: bool = True,
        auto_popup: bool = False,
    ) -> None:
        """Initialize chat functionality.

        Args:
            app_context: Application context for the chat.
            app_name: Application name for session persistence.
            add_to_toolbar: Whether to add quick bar to toolbar.
            auto_popup: Whether to show chat dock on launch.
        """
        # Create chat dock widget
        self._chat_dock = ChatDockWidget(
            app_context=app_context,
            app_name=app_name,
            parent=self,
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._chat_dock)

        # Load settings
        settings = get_settings()

        # Add quick bar to toolbar if requested
        if add_to_toolbar and hasattr(self, "addToolBar"):
            self._add_chat_quick_bar(app_context, app_name)

        # Auto-popup on first launch or if configured
        if auto_popup or settings.get("auto_popup", False):
            self._chat_dock.show()

        # Restore dock state from settings
        self._restore_dock_state(app_name)

    def _add_chat_quick_bar(self, app_context: str, app_name: str) -> None:
        """Add the chat quick bar to the toolbar."""
        if not hasattr(self, "addToolBar"):
            return

        self._quick_bar = ChatQuickBar(
            app_context=app_context,
            app_name=app_name,
            parent=self,
        )
        self._quick_bar.message_sent.connect(self._on_quick_message)
        self._quick_bar.chat_expanded.connect(self._show_chat_dock)

        # Create toolbar if needed
        if not hasattr(self, "_chat_toolbar"):
            self._chat_toolbar = self.addToolBar("Chat")
            self._chat_toolbar.setObjectName("chat_toolbar")

        # Add quick bar as widget action
        action = QWidgetAction(self)
        action.setDefaultWidget(self._quick_bar)
        self._chat_toolbar.addAction(action)

    def _on_quick_message(self, message: str) -> None:
        """Handle message from quick bar."""
        # For now, just expand the full chat
        # Future: could send to agent directly and show toast response
        self._show_chat_dock()
        if self._chat_dock:
            # Pre-populate input with message
            pass  # ChatDockWidget would handle this

    def _show_chat_dock(self) -> None:
        """Show the chat dock widget."""
        if self._chat_dock:
            self._chat_dock.show()
            self._chat_dock.raise_()

    def _save_dock_state(self, app_name: str) -> None:
        """Save dock state to settings."""
        # Implementation would save visible state
        pass

    def _restore_dock_state(self, app_name: str) -> None:
        """Restore dock state from settings."""
        # Implementation would restore visible state
        pass

    def closeEvent(self, event: QEvent) -> None:
        """Handle window close event."""
        # Save dock state before closing
        if hasattr(self, "_chat_dock") and self._chat_dock:
            self._save_dock_state(getattr(self, "_app_name", "upstream_drift"))
        super().closeEvent(event)  # type: ignore[misc]


def create_chat_toolbar(
    app_context: str = "default",
    app_name: str = "upstream_drift",
    parent: QWidget | None = None,
) -> QToolBar:
    """Create a toolbar with chat quick bar.

    Args:
        app_context: Application context for chat.
        app_name: Application name for session persistence.
        parent: Parent widget.

    Returns:
        Toolbar with chat quick bar embedded.
    """
    toolbar = QToolBar("Chat", parent)
    toolbar.setObjectName("chat_toolbar")

    quick_bar = ChatQuickBar(
        app_context=app_context,
        app_name=app_name,
        parent=parent,
    )

    action = QWidgetAction(parent)
    action.setDefaultWidget(quick_bar)
    toolbar.addAction(action)

    return toolbar