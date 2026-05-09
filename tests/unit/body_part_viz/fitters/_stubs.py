"""Shared stub shape for fitter tests."""

from __future__ import annotations

import numpy as np

from src.shared.python.body_part_viz._types import FittedShape


class StubShape:
    """Minimal duck-typed BodyPartShape for fitter tests."""

    def __init__(self, shape_id: str = "stub") -> None:
        self.shape_id = shape_id
        self.rest_dimensions: tuple[float, ...] = (1.0,)

    def vertices_at_rest(self) -> np.ndarray:
        return np.array([[0.0, 0.0, 0.0]])

    def faces(self) -> np.ndarray:
        return np.zeros((0, 3), dtype=np.int64)

    def transform(self, fitted: FittedShape) -> np.ndarray:
        return np.zeros((fitted.n_frames, 1, 3))
