"""Parity tests for upstream_mesh.fit_bounding_sphere."""

from __future__ import annotations

import numpy as np
import pytest

upstream_mesh = pytest.importorskip(
    "upstream_mesh",
    reason=(
        "upstream_mesh wheel not installed "
        "(run: maturin develop -m rust_core/upstream-mesh/Cargo.toml --features python)"
    ),
)

pytestmark = pytest.mark.unit


def test_fit_bounding_sphere_matches_numpy_reference() -> None:
    center = (1.0, 2.0, 3.0)
    vertices = np.array(
        [
            [2.0, 2.0, 3.0],
            [1.0, 4.0, 3.0],
            [1.0, 2.0, -1.0],
        ],
        dtype=np.float32,
    )
    volume = 10.0

    fit = upstream_mesh.fit_bounding_sphere(
        [tuple(row) for row in vertices.tolist()],
        center,
        volume,
    )

    reference_radius = float(
        np.sqrt(
            np.max(
                np.einsum(
                    "ij,ij->i", vertices - np.array(center), vertices - np.array(center)
                )
            )
        )
    )
    sphere_volume = (4 / 3) * np.pi * reference_radius**3
    assert fit.center == pytest.approx(center)
    assert fit.radius == pytest.approx(reference_radius)
    assert fit.volume_ratio == pytest.approx(volume / sphere_volume)
    assert fit.error_metric == pytest.approx(1.0 - volume / sphere_volume)


def test_fit_bounding_sphere_rejects_empty_vertices() -> None:
    with pytest.raises(ValueError, match="at least one vertex"):
        upstream_mesh.fit_bounding_sphere([], (0.0, 0.0, 0.0), 1.0)
