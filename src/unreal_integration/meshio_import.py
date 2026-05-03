"""Meshio-backed import for deterministic finite-element mesh reloading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.unreal_integration.mesh_loader import MeshLoadError

SUPPORTED_MESHIO_CELL_TYPES = frozenset(
    {
        "line",
        "triangle",
        "quad",
        "tetra",
        "hexahedron",
        "wedge",
        "pyramid",
    }
)


@dataclass(frozen=True)
class MeshioCellBlock:
    """A supported meshio cell block with optional physical group IDs."""

    cell_type: str
    cells: np.ndarray
    physical_group_ids: np.ndarray


@dataclass(frozen=True)
class MeshioImportedMesh:
    """Parsed meshio mesh data with nodes and supported cell blocks.

    Postconditions:
        - nodes is an ``N x 3`` array.
        - each cell block contains first-order supported cells only.
        - physical_group_ids has one entry per cell, using ``-1`` when absent.
    """

    nodes: np.ndarray
    cell_blocks: tuple[MeshioCellBlock, ...]


def load_meshio_cells(path: Path) -> MeshioImportedMesh:
    """Load nodes, supported cells, and physical group IDs through meshio.

    Raises:
        MeshLoadError: If meshio is unavailable, parsing fails, or the mesh
            contains unsupported cell types.
    """
    if path is None:
        raise ValueError("path must be provided")

    try:
        import meshio
    except ImportError as e:
        raise MeshLoadError(
            "Gmsh .msh import requires meshio>=5.3.5",
            str(path),
            e,
        ) from e

    try:
        mesh = meshio.read(path)
    except Exception as e:
        raise MeshLoadError(
            f"Failed to read mesh with meshio: {e}", str(path), e
        ) from e

    nodes = np.asarray(mesh.points, dtype=float)
    if nodes.ndim != 2 or nodes.shape[1] != 3:
        raise MeshLoadError("meshio mesh points must be an N x 3 array", str(path))

    physical_data = mesh.cell_data_dict.get("gmsh:physical", {})
    blocks: list[MeshioCellBlock] = []
    for cell_block in mesh.cells:
        cell_type = cell_block.type
        if cell_type not in SUPPORTED_MESHIO_CELL_TYPES:
            supported = ", ".join(sorted(SUPPORTED_MESHIO_CELL_TYPES))
            raise MeshLoadError(
                f"Unsupported mesh cell type '{cell_type}'. Supported: {supported}",
                str(path),
            )

        cells = np.asarray(cell_block.data, dtype=int)
        physical_group_ids = _physical_ids_for_block(
            physical_data.get(cell_type),
            cell_count=len(cells),
        )
        blocks.append(
            MeshioCellBlock(
                cell_type=cell_type,
                cells=cells,
                physical_group_ids=physical_group_ids,
            )
        )

    return MeshioImportedMesh(nodes=nodes, cell_blocks=tuple(blocks))


def _physical_ids_for_block(
    ids: np.ndarray | None,
    *,
    cell_count: int,
) -> np.ndarray:
    if ids is None:
        return np.full(cell_count, -1, dtype=int)

    physical_group_ids = np.asarray(ids, dtype=int)
    if physical_group_ids.shape != (cell_count,):
        raise MeshLoadError(
            "gmsh:physical cell data must contain one physical group ID per cell"
        )
    return physical_group_ids
