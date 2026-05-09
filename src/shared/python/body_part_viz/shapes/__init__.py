"""Body-part shapes (primitives, mesh, composite).

Concrete implementations:

- #4759 — primitives (Line, Cylinder, Ellipsoid, Capsule, Composite)
- #4758 — :class:`MeshShape` with STL/OBJ/PLY/GLB loaders via trimesh
  (added in a follow-up issue of EPIC #4755)
"""

from __future__ import annotations

from src.shared.python.body_part_viz.shapes.primitives import (
    CapsuleShape,
    CompositeShape,
    CylinderShape,
    EllipsoidShape,
    LineShape,
)

__all__ = [
    "CapsuleShape",
    "CompositeShape",
    "CylinderShape",
    "EllipsoidShape",
    "LineShape",
]
