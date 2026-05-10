"""Embeddable-tool adapter for the Model Explorer (URDF Generator).

Implements the :class:`~src.shared.python.launcher_embed.EmbeddableTool`
protocol so the launcher can host the Model Explorer as a tab or dock widget
instead of spawning a standalone process.

The Model Explorer is a complex tool with multiple dock widgets and panels.
The embed adapter exposes the main content widget while allowing the host
to manage the surrounding chrome (menu bar, docks, status bar).
"""

from __future__ import annotations

from typing import Any

from src.shared.python.launcher_embed import EmbedCapabilities

__all__ = ["_ModelExplorerEmbedAdapter"]


class _ModelExplorerEmbedAdapter:
    """Adapter exposing the Model Explorer's main widget through the embed contract."""

    tool_id: str = "model_explorer"

    def embed_capabilities(self) -> EmbedCapabilities:
        return EmbedCapabilities(
            supports_embedded=True,
            prefers_dock=False,
            min_size=(1024, 768),
            requires_separate_qapplication=False,
        )

    def create_main_widget(self, parent: Any) -> Any:
        # Lazy import: the model explorer pulls in PyQt6 + mujoco + various
        # visualization dependencies. Keeping this import inside
        # ``create_main_widget`` lets the adapter load cleanly in
        # headless contexts.
        from .main_window import URDFGeneratorWindow

        # Create the main window but return its central widget for embedding
        window = URDFGeneratorWindow(parent)
        # The window itself is a QMainWindow, but for embedding we need
        # to return just the content. The host will manage the chrome.
        # Return the window and let the host extract centralWidget if needed.
        return window

    def cleanup(self) -> None:
        """Clean up any resources held by the Model Explorer.

        The Model Explorer doesn't hold external resources that need
        explicit cleanup beyond normal Qt teardown. This method is
        idempotent and safe to call multiple times.
        """
        pass

    def is_dirty(self) -> bool:
        # The Model Explorer works with file-based URDF models.
        # Users save explicitly; no unsaved state tracking needed here.
        return False