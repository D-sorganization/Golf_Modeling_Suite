"""Embeddable-tool adapter for the C3D Viewer.

Implements the :class:`~src.shared.python.launcher_embed.EmbeddableTool`
protocol so the launcher can host the C3D viewer as a tab or dock widget
instead of spawning a standalone process.

The viewer uses matplotlib canvases inside its plot tabs. :meth:`cleanup`
releases all matplotlib figures scoped to the C3D viewer widget so closing
the embedded tab does not leak figure references in the host process.
"""

from __future__ import annotations

from typing import Any

from src.shared.python.launcher_embed import EmbedCapabilities

__all__ = ["_C3DViewerEmbedAdapter"]


class _C3DViewerEmbedAdapter:
    """Adapter exposing the C3D viewer's ``MainWidget`` through the embed contract."""

    tool_id: str = "c3d_viewer"

    def embed_capabilities(self) -> EmbedCapabilities:
        return EmbedCapabilities(
            supports_embedded=True,
            prefers_dock=False,
            min_size=(900, 600),
            requires_separate_qapplication=False,
        )

    def create_main_widget(self, parent: Any) -> Any:
        # Lazy import: the viewer pulls in PyQt6 + matplotlib + the C3D
        # reader chain. Keeping this import inside ``create_main_widget``
        # lets the adapter (and therefore the registry side-effect at
        # import time) load cleanly in headless contexts.
        from .c3d_viewer import MainWidget

        return MainWidget(parent)

    def cleanup(self) -> None:
        """Release matplotlib figures held by the C3D viewer widget.

        Must be idempotent and scoped to only this widget's figures.
        Wrapped in a defensive try/except so a misbehaving matplotlib
        never blocks host shutdown.
        """
        try:
            import matplotlib.pyplot as plt

            # Close only figures created by this C3D viewer widget
            # by iterating through managed tab figures
            from .c3d_viewer import MainWidget

            # Get all current figure numbers before closing
            current_figs = plt.get_fignums()
            for fig_num in current_figs:
                fig = plt.figure(fig_num)
                # Check if this figure's canvas parent chain contains
                # a C3D viewer widget
                canvas = getattr(fig, "canvas", None)
                if canvas is not None:
                    parent = canvas.parent()
                    is_c3d_figure = False
                    while parent is not None:
                        if isinstance(parent, MainWidget):
                            is_c3d_figure = True
                            break
                        parent = parent.parent()
                    if is_c3d_figure:
                        plt.close(fig_num)
        except Exception:  # pragma: no cover - defensive
            # Host shutdown must not depend on us. Swallow rather than
            # raise; the registry contract requires ``cleanup`` to be
            # idempotent and non-fatal.
            pass

    def is_dirty(self) -> bool:
        # The C3D viewer is read-only on the input C3D file; the export
        # dialog writes to a user-chosen path each time. Nothing to
        # prompt the user about on close.
        return False