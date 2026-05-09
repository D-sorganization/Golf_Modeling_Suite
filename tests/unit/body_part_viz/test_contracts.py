"""Tests for ``body_part_viz.contracts``.

Confirms that:

- The three Protocols (`BodyPartShape`, `ShapeFitter`, `ShapeRenderer`) are
  ``@runtime_checkable``.
- A duck-typed implementation passes ``isinstance()`` checks.
- The module's public API is what we expect.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import (
    BodyPartShape,
    ShapeFitter,
    ShapeRenderer,
)
from src.shared.python.body_part_viz.theme import ShapeTheme


# ---------------------------------------------------------------------------
# BodyPartShape
# ---------------------------------------------------------------------------


class _StubShape:
    """Minimal duck-typed BodyPartShape for protocol verification."""

    shape_id = "stub"
    rest_dimensions = (1.0,)

    def vertices_at_rest(self) -> np.ndarray:
        return np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    def faces(self) -> np.ndarray:
        return np.zeros((0, 3), dtype=np.int64)

    def transform(self, fitted: FittedShape) -> np.ndarray:
        T = fitted.n_frames
        V = self.vertices_at_rest().shape[0]
        return np.zeros((T, V, 3))


@pytest.mark.unit
def test_stub_shape_satisfies_body_part_shape_protocol() -> None:
    assert isinstance(_StubShape(), BodyPartShape)


@pytest.mark.unit
def test_object_missing_methods_fails_protocol() -> None:
    class _Bad:
        shape_id = "bad"
        rest_dimensions = (1.0,)

    assert not isinstance(_Bad(), BodyPartShape)


# ---------------------------------------------------------------------------
# ShapeFitter
# ---------------------------------------------------------------------------


class _StubFitter:
    """Identity fitter for protocol verification."""

    def fit(
        self,
        shape: BodyPartShape,
        binding: MarkerBinding,
        markers_xyz: dict[str, np.ndarray],
    ) -> FittedShape:
        n_frames = next(iter(markers_xyz.values())).shape[0]
        return FittedShape(
            shape_id=shape.shape_id,
            binding=binding,
            centroid=np.zeros((n_frames, 3)),
            rotation_matrix=np.tile(np.eye(3), (n_frames, 1, 1)),
            scale=np.ones((n_frames, 3)),
            valid_mask=np.ones(n_frames, dtype=bool),
        )


@pytest.mark.unit
def test_stub_fitter_satisfies_shape_fitter_protocol() -> None:
    assert isinstance(_StubFitter(), ShapeFitter)


@pytest.mark.unit
def test_stub_fitter_round_trip() -> None:
    """Stub fitter actually produces a valid FittedShape."""
    fitter = _StubFitter()
    shape = _StubShape()
    binding = MarkerBinding(BindingKind.BETWEEN_TWO, ("a", "b"))
    markers = {
        "a": np.zeros((5, 3)),
        "b": np.array([[1.0, 0.0, 0.0]] * 5),
    }
    fit = fitter.fit(shape, binding, markers)
    assert fit.shape_id == "stub"
    assert fit.n_frames == 5


# ---------------------------------------------------------------------------
# ShapeRenderer
# ---------------------------------------------------------------------------


class _StubRenderer:
    """In-memory renderer that satisfies the protocol."""

    def __init__(self) -> None:
        self._handles: dict[str, tuple[BodyPartShape, FittedShape, ShapeTheme]] = {}
        self._visible: dict[str, bool] = {}
        self._frame: dict[str, int] = {}

    def add_shape(
        self,
        shape: BodyPartShape,
        fitted: FittedShape,
        theme: ShapeTheme,
    ) -> str:
        if shape.shape_id != fitted.shape_id:
            raise ValueError("shape.shape_id != fitted.shape_id")
        handle = f"h{len(self._handles)}"
        self._handles[handle] = (shape, fitted, theme)
        self._visible[handle] = True
        self._frame[handle] = 0
        return handle

    def update_frame(self, handle: str, frame_idx: int) -> None:
        if handle not in self._handles:
            raise KeyError(handle)
        _, fitted, _ = self._handles[handle]
        if not 0 <= frame_idx < fitted.n_frames:
            raise IndexError(frame_idx)
        self._frame[handle] = frame_idx

    def set_visible(self, handle: str, visible: bool) -> None:
        if handle not in self._handles:
            raise KeyError(handle)
        self._visible[handle] = visible

    def remove(self, handle: str) -> None:
        # Idempotent.
        self._handles.pop(handle, None)
        self._visible.pop(handle, None)
        self._frame.pop(handle, None)


@pytest.mark.unit
def test_stub_renderer_satisfies_shape_renderer_protocol() -> None:
    assert isinstance(_StubRenderer(), ShapeRenderer)


@pytest.mark.unit
def test_stub_renderer_lifecycle() -> None:
    """Sanity: the stub renderer's add/update/visible/remove all work."""
    renderer = _StubRenderer()
    shape = _StubShape()
    binding = MarkerBinding(BindingKind.BETWEEN_TWO, ("a", "b"))
    fitted = FittedShape(
        shape_id="stub",
        binding=binding,
        centroid=np.zeros((3, 3)),
        rotation_matrix=np.tile(np.eye(3), (3, 1, 1)),
        scale=np.ones((3, 3)),
        valid_mask=np.ones(3, dtype=bool),
    )
    theme = ShapeTheme()

    handle = renderer.add_shape(shape, fitted, theme)
    assert isinstance(handle, str)

    renderer.update_frame(handle, 1)
    renderer.set_visible(handle, False)

    with pytest.raises(IndexError):
        renderer.update_frame(handle, 99)

    with pytest.raises(KeyError):
        renderer.update_frame("nonexistent", 0)

    renderer.remove(handle)
    renderer.remove(handle)  # idempotent

    with pytest.raises(KeyError):
        renderer.update_frame(handle, 0)


@pytest.mark.unit
def test_renderer_rejects_shape_id_mismatch() -> None:
    renderer = _StubRenderer()
    shape = _StubShape()
    binding = MarkerBinding(BindingKind.BETWEEN_TWO, ("a", "b"))
    wrong = FittedShape(
        shape_id="other",
        binding=binding,
        centroid=np.zeros((1, 3)),
        rotation_matrix=np.tile(np.eye(3), (1, 1, 1)),
        scale=np.ones((1, 3)),
        valid_mask=np.ones(1, dtype=bool),
    )
    with pytest.raises(ValueError, match="shape_id"):
        renderer.add_shape(shape, wrong, ShapeTheme())
