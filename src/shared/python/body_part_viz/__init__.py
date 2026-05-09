"""Body-part visualisation toolkit.

A cross-tool, cross-renderer package for displaying body segments as
geometric shapes (lines, cylinders, ellipsoids, capsules, meshes) bound
to mocap markers. Used by the C3D viewer, motion-match preview, and
URDF generator.

This top-level module exposes only **contracts and dataclasses**.
Concrete shapes, fitters, and renderers live in sibling sub-packages
and are added in subsequent issues:

- :mod:`body_part_viz.shapes` — primitives (#4759) + meshes (#4758)
- :mod:`body_part_viz.fitters` — fitter implementations (#4756)
- :mod:`body_part_viz.renderers` — matplotlib (#4760) + pyqtgraph (#4762)

Public API
----------

- :class:`BodyPartShape`, :class:`ShapeFitter`, :class:`ShapeRenderer`
  — protocols
- :class:`MarkerBinding`, :class:`BindingKind` — how shapes attach to
  markers
- :class:`ShapeTheme` — visual styling (color, opacity, edges)
- :class:`FittedShape` — per-frame placement trajectory

See the EPIC tracking issue #4755 for the campaign overview.
"""

from __future__ import annotations

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import (
    BodyPartShape,
    ShapeFitter,
    ShapeRenderer,
)
from src.shared.python.body_part_viz.theme import ShapeTheme

__all__ = [
    "BindingKind",
    "BodyPartShape",
    "FittedShape",
    "MarkerBinding",
    "ShapeFitter",
    "ShapeRenderer",
    "ShapeTheme",
]
