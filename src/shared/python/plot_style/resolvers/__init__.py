"""ColorResolver implementations sub-package.

Concrete :class:`~src.shared.python.plot_style.contracts.ColorResolver`
implementations:

* :class:`StaticColorResolver` — passes through the constant RGBA of a
  :class:`StaticColor`.
* :class:`PaletteColorResolver` — looks up a named palette by index
  (matplotlib palettes plus a project-local custom registry).
* :class:`DataDrivenColorResolver` — normalises a
  :class:`DataChannel` through ``vmin`` / ``vmax`` and samples a
  matplotlib colormap (with bulk LUT pre-computation for the hot path).
"""

from __future__ import annotations

from .data_driven import DataDrivenColorResolver
from .palette import (
    PaletteColorResolver,
    list_custom_palettes,
    register_palette,
    unregister_palette,
)
from .static import StaticColorResolver

__all__ = [
    "DataDrivenColorResolver",
    "PaletteColorResolver",
    "StaticColorResolver",
    "list_custom_palettes",
    "register_palette",
    "unregister_palette",
]
