from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from src.shared.python.humanoid_character_builder.mesh._cg_primitive_fitting import (
    fit_sphere,
)


def test_fit_sphere_uses_upstream_mesh_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMesh:
        centroid = np.array([1.0, 2.0, 3.0], dtype=float)
        vertices = np.array([[2.0, 2.0, 3.0], [1.0, 4.0, 3.0]], dtype=float)
        volume = 7.0

    calls = []

    def fit_bounding_sphere(
        vertices: list[tuple[float, float, float]],
        center: tuple[float, float, float],
        mesh_volume: float,
    ) -> SimpleNamespace:
        calls.append((vertices, center, mesh_volume))
        return SimpleNamespace(
            center=center,
            radius=2.0,
            volume_ratio=0.75,
            error_metric=0.25,
        )

    monkeypatch.setitem(
        sys.modules,
        "upstream_mesh",
        SimpleNamespace(fit_bounding_sphere=fit_bounding_sphere),
    )

    fit = fit_sphere(FakeMesh())

    assert calls == [
        (
            [(2.0, 2.0, 3.0), (1.0, 4.0, 3.0)],
            (1.0, 2.0, 3.0),
            7.0,
        )
    ]
    assert fit.primitive_type == "sphere"
    assert fit.center == (1.0, 2.0, 3.0)
    assert fit.dimensions == (2.0,)
    assert fit.volume_ratio == 0.75
    assert fit.error_metric == 0.25


def test_fit_sphere_keeps_numpy_fallback_without_upstream_mesh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMesh:
        centroid = np.array([0.0, 0.0, 0.0], dtype=float)
        vertices = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]], dtype=float)
        volume = 4.0

    monkeypatch.delitem(sys.modules, "upstream_mesh", raising=False)

    fit = fit_sphere(FakeMesh())

    assert fit.primitive_type == "sphere"
    assert fit.center == (0.0, 0.0, 0.0)
    assert fit.dimensions == (2.0,)
    sphere_volume = (4 / 3) * np.pi * 2.0**3
    assert fit.volume_ratio == pytest.approx(4.0 / sphere_volume)
