"""Palette color resolver.

A :class:`PaletteColorResolver` looks up the ``palette_index`` slot of a
:class:`PaletteColor` in a named matplotlib palette (``tab10``,
``tab20``, ``Set2``, ...) or in a project-local custom-palette registry,
and returns the resulting RGBA tuple. The bulk path broadcasts that
single tuple over the requested ``(n_frames, [n_markers,] 4)`` shape.

Custom palettes
---------------
The module-level :func:`register_palette` / :func:`unregister_palette`
helpers manage a small registry of user-defined palettes. Registered
palettes shadow matplotlib palettes of the same name, allowing a
project to (for example) ship a brand-color palette under the friendly
name ``"brand"`` without depending on a matplotlib release.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Colormap, is_color_like, to_rgba

from .._types import RGBATuple
from ..colors import ColorScale, PaletteColor

__all__ = [
    "PaletteColorResolver",
    "list_custom_palettes",
    "register_palette",
    "unregister_palette",
]


# Name -> tuple of RGBA tuples. Stored in fully-materialised form so
# lookup never has to re-parse hex strings.
_CUSTOM_PALETTES: dict[str, tuple[RGBATuple, ...]] = {}


def register_palette(name: str, colors: Sequence[str]) -> None:
    """Register a custom palette under ``name``.

    Parameters
    ----------
    name:
        Non-empty palette identifier. Subsequent registrations with the
        same name overwrite the previous mapping.
    colors:
        Sequence of at least one matplotlib-recognised color string.
        Each entry is parsed eagerly and stored as a 4-tuple of floats.
    """
    if not isinstance(name, str) or not name:
        raise ValueError(f"name must be a non-empty string; got {name!r}")
    if not isinstance(colors, Sequence) or isinstance(colors, (str, bytes)):
        raise TypeError(
            f"colors must be a sequence of strings; got {type(colors).__name__}"
        )
    if len(colors) == 0:
        raise ValueError("colors must contain at least one entry")

    parsed: list[RGBATuple] = []
    for index, color in enumerate(colors):
        if not isinstance(color, str) or not color:
            raise ValueError(
                f"color at index {index} must be a non-empty string; got {color!r}"
            )
        if not is_color_like(color):
            raise ValueError(
                f"color {color!r} at index {index} is not a parseable matplotlib color"
            )
        rgba = to_rgba(cast(Any, color))
        parsed.append((float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])))
    _CUSTOM_PALETTES[name] = tuple(parsed)


def unregister_palette(name: str) -> None:
    """Remove ``name`` from the custom palette registry.

    No-op if ``name`` is not registered.
    """
    _CUSTOM_PALETTES.pop(name, None)


def list_custom_palettes() -> tuple[str, ...]:
    """Return the names of all currently registered custom palettes."""
    return tuple(sorted(_CUSTOM_PALETTES))


def _matplotlib_palette_size(cmap: Colormap) -> int:
    """Return the number of distinct colors in a qualitative palette."""
    size = getattr(cmap, "N", 0) or 0
    if size <= 0:
        return 256  # continuous fallback
    return int(size)


def _available_palettes() -> tuple[str, ...]:
    """Return the union of custom and matplotlib palette names."""
    builtins = tuple(sorted(colormaps))
    return tuple(sorted(set(builtins) | set(_CUSTOM_PALETTES)))


def _resolve_palette_color(palette_name: str, palette_index: int) -> RGBATuple:
    """Look up the RGBA at ``palette_index`` in ``palette_name``.

    Custom palettes shadow matplotlib palettes of the same name. The
    function raises :class:`ValueError` (with the offending parameters
    in the message) on:

    * unknown palette name,
    * negative ``palette_index``,
    * ``palette_index`` ≥ palette size for *qualitative* (small)
      matplotlib palettes — listing the palette length so the caller
      can fix the index.
    """
    if palette_index < 0:
        raise ValueError(f"palette_index must be non-negative; got {palette_index}")

    # Custom registry has priority.
    if palette_name in _CUSTOM_PALETTES:
        entries = _CUSTOM_PALETTES[palette_name]
        if palette_index >= len(entries):
            raise ValueError(
                f"palette_index {palette_index} out of range for custom "
                f"palette {palette_name!r} of length {len(entries)}"
            )
        return entries[palette_index]

    if palette_name not in colormaps:
        available = _available_palettes()
        raise ValueError(
            f"unknown palette {palette_name!r}; available palettes: {list(available)}"
        )

    cmap = cast(Colormap, colormaps[palette_name])
    size = _matplotlib_palette_size(cmap)
    # Qualitative palettes (tab10, Set2, ...) have small N; reject OOB
    # so callers see configuration errors fast. Continuous palettes
    # (viridis, ...) have N = 256, which is effectively unbounded for
    # categorical use, so we let them wrap modulo size.
    if size <= 32 and palette_index >= size:
        raise ValueError(
            f"palette_index {palette_index} out of range for palette "
            f"{palette_name!r} of length {size}"
        )
    rgba = cmap(palette_index % size)
    return (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))


class PaletteColorResolver:
    """Resolver for :class:`PaletteColor` scales.

    Implements the
    :class:`~src.shared.python.plot_style.contracts.ColorResolver`
    Protocol.
    """

    def resolve_one(
        self,
        scale: ColorScale,
        frame_idx: int,
        marker_idx: int | None = None,
    ) -> tuple[float, float, float, float]:
        """Return the palette color for ``scale``.

        ``frame_idx`` and ``marker_idx`` are accepted for Protocol
        compatibility and ignored — palette colors are constant.
        """
        del frame_idx, marker_idx  # interface compatibility
        if not isinstance(scale, PaletteColor):
            raise TypeError(
                "PaletteColorResolver only accepts PaletteColor; "
                f"got {type(scale).__name__}"
            )
        return _resolve_palette_color(scale.palette_name, scale.palette_index)

    def resolve_array(
        self,
        scale: ColorScale,
        n_frames: int,
        n_markers: int | None = None,
    ) -> np.ndarray:
        """Return a broadcast ``(n_frames, [n_markers,] 4)`` RGBA array."""
        if not isinstance(scale, PaletteColor):
            raise TypeError(
                "PaletteColorResolver only accepts PaletteColor; "
                f"got {type(scale).__name__}"
            )
        if not isinstance(n_frames, int) or n_frames <= 0:
            raise ValueError(f"n_frames must be a positive int; got {n_frames!r}")
        if n_markers is not None and (not isinstance(n_markers, int) or n_markers <= 0):
            raise ValueError(
                f"n_markers must be a positive int or None; got {n_markers!r}"
            )

        rgba = np.asarray(
            _resolve_palette_color(scale.palette_name, scale.palette_index),
            dtype=np.float64,
        )
        if n_markers is None:
            out = np.broadcast_to(rgba, (n_frames, 4)).copy()
        else:
            out = np.broadcast_to(rgba, (n_frames, n_markers, 4)).copy()
        return out
