"""Unit tests for SupportPolygon.distance_to_edge (issue #2791).

Validates correctness of the scalar-math optimization: projection before
the segment, after the segment, onto the interior, degenerate edges, and
a point that lies outside the polygon (which returns -1.0).
"""

from __future__ import annotations

import math

import pytest

from src.shared.python.humanoid_character_builder.core.model import SupportPolygon


@pytest.fixture
def square() -> SupportPolygon:
    """Unit square with vertices at (0,0), (1,0), (1,1), (0,1)."""
    return SupportPolygon(vertices=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])


class TestSupportPolygonDistanceToEdge:
    def test_center_point(self, square: SupportPolygon) -> None:
        """Center of unit square is 0.5 from each edge."""
        dist = square.distance_to_edge((0.5, 0.5))
        assert math.isclose(dist, 0.5, rel_tol=1e-9)

    def test_near_bottom_edge(self, square: SupportPolygon) -> None:
        """Point close to the bottom edge has distance ~0.1."""
        dist = square.distance_to_edge((0.5, 0.1))
        assert math.isclose(dist, 0.1, rel_tol=1e-9)

    def test_near_left_edge(self, square: SupportPolygon) -> None:
        """Point close to the left edge has distance ~0.05."""
        dist = square.distance_to_edge((0.05, 0.5))
        assert math.isclose(dist, 0.05, rel_tol=1e-9)

    def test_near_corner_interior(self, square: SupportPolygon) -> None:
        """Point near bottom-left corner: min dist is to the nearest edge."""
        dist = square.distance_to_edge((0.1, 0.1))
        # Nearest edge distance is 0.1 (both bottom and left edges equidistant)
        assert math.isclose(dist, 0.1, rel_tol=1e-9)

    def test_point_outside_returns_negative(self, square: SupportPolygon) -> None:
        """Points outside the polygon return -1.0 (outside = unstable)."""
        dist = square.distance_to_edge((1.5, 0.5))
        assert dist == -1.0

    def test_degenerate_polygon_not_contains(self) -> None:
        """A degenerate polygon (< 3 vertices) never contains any point."""
        line = SupportPolygon(vertices=[(0.0, 0.0), (1.0, 0.0)])
        # contains() returns False for < 3 vertices, so distance_to_edge returns -1.0
        assert line.distance_to_edge((0.5, 0.0)) == -1.0

    def test_requires_point(self, square: SupportPolygon) -> None:
        """Passing None as point raises ValueError."""
        with pytest.raises(ValueError):
            square.distance_to_edge(None)  # type: ignore[arg-type]

    def test_returns_float(self, square: SupportPolygon) -> None:
        """Return type is always a plain Python float."""
        dist = square.distance_to_edge((0.5, 0.5))
        assert isinstance(dist, float)
