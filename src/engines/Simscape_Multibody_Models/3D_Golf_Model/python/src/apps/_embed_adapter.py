"""Embeddable-tool adapter for the C3D Motion Analysis viewer.

Implements the :class:`~src.shared.python.launcher_embed.EmbeddableTool`
protocol so the launcher can host the viewer as a tab or dock widget
instead of spawning a standalone process.

The viewer uses matplotlib canvases inside its plot tabs. :meth:`cleanup`
releases only the figures owned by widgets this adapter created — it
does **not** call ``plt.close('all')`` because that would also tear
down figures owned by other embedded tools sharing the host process
(see review feedback on #5062).
"""

from __future__ import annotations

from typing import Any

from src.shared.python.launcher_embed import EmbedCapabilities

__all__ = ["_C3DViewerEmbedAdapter"]


class _C3DViewerEmbedAdapter:
    """Adapter exposing the viewer's ``MainWidget`` through the embed contract."""

    tool_id: str = "c3d_viewer"

    def __init__(self) -> None:
        # Track every ``MainWidget`` instance we hand to the host so
        # ``cleanup`` can scope figure release to just our widgets'
        # canvases instead of nuking every matplotlib figure in the
        # process (which would also close figures owned by sibling
        # embedded tools — see #5062).
        self._created_widgets: list[Any] = []

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

        widget = MainWidget(parent)
        self._created_widgets.append(widget)
        return widget

    def cleanup(self) -> None:
        """Release matplotlib figures held by *our* plot tabs only.

        Walks every ``MainWidget`` we created, finds its embedded
        ``FigureCanvasQTAgg`` children, and closes each figure
        individually. Wrapped in a defensive try/except so a misbehaving
        matplotlib never blocks host shutdown, and idempotent so the
        host can call cleanup more than once.
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

            for widget in list(self._created_widgets):
                try:
                    canvases = widget.findChildren(FigureCanvasQTAgg)
                except Exception:  # pragma: no cover - widget may be deleted
                    continue
                for canvas in canvases:
                    try:
                        plt.close(canvas.figure)
                    except Exception:  # pragma: no cover - defensive
                        pass
        except Exception:  # pragma: no cover - defensive
            # Host shutdown must not depend on us. Swallow rather than
            # raise; the registry contract requires ``cleanup`` to be
            # idempotent and non-fatal.
            pass
        finally:
            self._created_widgets.clear()

    def is_dirty(self) -> bool:
        # The viewer is read-only on the input C3D file; the export
        # dialog writes to a user-chosen path each time. Nothing to
        # prompt the user about on close.
        return False
