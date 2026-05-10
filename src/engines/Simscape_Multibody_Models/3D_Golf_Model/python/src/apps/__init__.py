"""C3D Viewer application package.

This package provides the C3D motion capture data viewer with embedded
widget support for the launcher's embedded host.

The :class:`_C3DViewerEmbedAdapter` is registered with the embeddable-tool
registry on import so the launcher can host the C3D viewer as a tab or dock
widget.
"""

from src.shared.python.launcher_embed import (
    EmbeddableTool,
    get_embeddable_tool,
    register_embeddable_tool,
)

from ._embed_adapter import _C3DViewerEmbedAdapter

# Module-level singleton: registries key on ``tool_id`` so a single
# instance is sufficient. Constructing the adapter is cheap (it does not
# spin up any resources until ``create_main_widget`` is called).
_ADAPTER: EmbeddableTool = _C3DViewerEmbedAdapter()

# Guard against double-import (e.g. test reloads). The registry rejects
# duplicate ids by design — we want a quiet no-op here instead.
if get_embeddable_tool(_ADAPTER.tool_id) is None:
    register_embeddable_tool(_ADAPTER)

__all__ = ["MainWidget", "C3DViewerMainWindow"]