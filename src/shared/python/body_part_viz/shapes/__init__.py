"""Body-part shapes (primitives, mesh, composite).

Concrete implementations land in:

- #4759 — primitives (Line, Cylinder, Ellipsoid, Capsule, Composite)
- #4758 — :class:`MeshShape` with STL/OBJ/PLY/GLB loaders via trimesh

This module is currently a placeholder so callers can write
``from body_part_viz.shapes import ...`` once implementations land.
"""

from __future__ import annotations

__all__: list[str] = []
