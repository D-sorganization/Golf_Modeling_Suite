"""Visual theme for body-part shapes.

Themes are intentionally small and stateless. They describe **how** a
shape is rendered (color, opacity, edge style) without committing to a
specific renderer backend.

Design by Contract
------------------
``__post_init__`` validates every invariant.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

__all__ = ["ShapeTheme"]


# Matplotlib's full color spec is rich; we accept a conservative subset
# that's easy to validate without importing matplotlib. Allowed forms:
#   - "#rgb" / "#rgba" / "#rrggbb" / "#rrggbbaa"
#   - named colors (any non-empty alphabetic identifier; downstream
#     renderers do the final validation)
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_NAMED_COLOR_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_:-]*$")


def _check_color(name: str, value: str) -> None:
    """Validate that *value* parses as either ``#hex`` or a named color."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be str, got {type(value).__name__}")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.startswith("#"):
        if not _HEX_COLOR_RE.match(value):
            raise ValueError(
                f"{name}={value!r} is not a valid hex color (#rgb / #rgba / "
                "#rrggbb / #rrggbbaa)"
            )
        return
    if not _NAMED_COLOR_RE.match(value):
        raise ValueError(
            f"{name}={value!r} is not a valid color (must be #hex or a named color)"
        )


@dataclass(frozen=True)
class ShapeTheme:
    """Visual styling for a body-part shape.

    Attributes:
        color: Fill color, either ``#hex`` or a named color string.
        opacity: Alpha in [0.0, 1.0].
        edge_color: Edge color, same format as ``color``.
        edge_width: Edge width in points; must be ``>= 0``.
        flat_shaded: True for flat shading, False for smooth (Gouraud).
        group: Logical grouping name; used by themed colour palettes.
            Must be a non-empty string.
    """

    color: str = "#1f77b4"
    opacity: float = 0.8
    edge_color: str = "#000000"
    edge_width: float = 0.5
    flat_shaded: bool = True
    group: str = "default"

    def __post_init__(self) -> None:
        _check_color("color", self.color)
        _check_color("edge_color", self.edge_color)

        if not isinstance(self.opacity, (int, float)):
            raise TypeError(f"opacity must be float, got {type(self.opacity).__name__}")
        if not math.isfinite(self.opacity):
            raise ValueError(f"opacity must be finite, got {self.opacity}")
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError(f"opacity must be in [0.0, 1.0], got {self.opacity}")

        if not isinstance(self.edge_width, (int, float)):
            raise TypeError(
                f"edge_width must be float, got {type(self.edge_width).__name__}"
            )
        if not math.isfinite(self.edge_width):
            raise ValueError(f"edge_width must be finite, got {self.edge_width}")
        if self.edge_width < 0.0:
            raise ValueError(f"edge_width must be >= 0, got {self.edge_width}")

        if not isinstance(self.flat_shaded, bool):
            raise TypeError(
                f"flat_shaded must be bool, got {type(self.flat_shaded).__name__}"
            )

        if not isinstance(self.group, str):
            raise TypeError(f"group must be str, got {type(self.group).__name__}")
        if not self.group:
            raise ValueError("group must be non-empty")
