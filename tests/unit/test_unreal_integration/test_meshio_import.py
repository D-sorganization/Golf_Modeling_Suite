"""Tests for deterministic meshio-backed mesh import."""

from __future__ import annotations

from pathlib import Path

import meshio
import numpy as np
import pytest
from src.unreal_integration.mesh_loader import MeshFormat, MeshLoader, MeshLoadError
from src.unreal_integration.meshio_import import load_meshio_cells


def _write_gmsh_mesh(
    path: Path,
    *,
    cells: list[tuple[str, np.ndarray]],
    physical_ids: list[np.ndarray],
) -> None:
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
        ]
    )
    mesh = meshio.Mesh(
        points=points,
        cells=cells,
        cell_data={"gmsh:physical": physical_ids},
    )
    meshio.write(path, mesh, file_format="gmsh22")


def test_load_meshio_cells_preserves_nodes_cells_and_physical_ids(
    tmp_path: Path,
) -> None:
    mesh_path = tmp_path / "mixed.msh"
    _write_gmsh_mesh(
        mesh_path,
        cells=[
            ("tetra", np.array([[0, 1, 2, 3]])),
            ("wedge", np.array([[0, 1, 2, 3, 5, 4]])),
        ],
        physical_ids=[np.array([11]), np.array([23])],
    )

    parsed = load_meshio_cells(mesh_path)

    assert parsed.nodes.shape == (6, 3)
    assert [block.cell_type for block in parsed.cell_blocks] == ["tetra", "wedge"]
    assert parsed.cell_blocks[0].cells.tolist() == [[0, 1, 2, 3]]
    assert parsed.cell_blocks[0].physical_group_ids.tolist() == [11]
    assert parsed.cell_blocks[1].cells.tolist() == [[0, 1, 2, 3, 5, 4]]
    assert parsed.cell_blocks[1].physical_group_ids.tolist() == [23]


def test_load_meshio_cells_fails_loudly_for_higher_order_cells(
    tmp_path: Path,
) -> None:
    mesh_path = tmp_path / "higher_order.msh"
    points = np.zeros((10, 3))
    mesh = meshio.Mesh(
        points=points,
        cells=[("tetra10", np.arange(10).reshape(1, 10))],
        cell_data={"gmsh:physical": [np.array([99])]},
    )
    meshio.write(mesh_path, mesh, file_format="gmsh22")

    with pytest.raises(MeshLoadError, match="Unsupported mesh cell type.*tetra10"):
        load_meshio_cells(mesh_path)


def test_mesh_loader_loads_msh_via_meshio_without_silent_cell_drops(
    tmp_path: Path,
) -> None:
    mesh_path = tmp_path / "ui_import.msh"
    _write_gmsh_mesh(
        mesh_path,
        cells=[
            ("tetra", np.array([[0, 1, 2, 3]])),
            ("wedge", np.array([[0, 1, 2, 3, 5, 4]])),
        ],
        physical_ids=[np.array([7]), np.array([8])],
    )

    loaded = MeshLoader(enable_cache=False).load(str(mesh_path))

    assert loaded.format == MeshFormat.MSH
    assert loaded.vertex_count == 6
    assert loaded.face_count == 2
    assert loaded.faces[0].cell_type == "tetra"
    assert loaded.faces[0].physical_group_id == 7
    assert loaded.faces[1].cell_type == "wedge"
    assert loaded.faces[1].physical_group_id == 8
