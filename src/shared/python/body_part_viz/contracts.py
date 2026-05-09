"""Protocols defining the body-part visualisation contracts.

This module is the **stable** surface of the package. Implementations
of shapes, fitters, and renderers will be added in sibling modules but
must always conform to the protocols here.

The protocols are :func:`runtime_checkable` so they integrate with
``isinstance()`` checks for unit-test verification of duck-typed
implementations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import MarkerBinding
from src.shared.python.body_part_viz.theme import ShapeTheme

__all__ = ["BodyPartShape", "ShapeFitter", "ShapeRenderer"]


@runtime_checkable
class BodyPartShape(Protocol):
    """A geometric body-part visualisation.

    Implementations: ``LineShape``, ``CylinderShape``, ``EllipsoidShape``,
    ``CapsuleShape``, ``MeshShape``, ``CompositeShape`` (added in
    later issues).

    Attributes:
        shape_id: Stable, human-readable identifier (e.g. ``"cylinder"``,
            ``"mesh:head_v1"``). Used as a dictionary key in renderers
            and persistence.
        rest_dimensions: Rest-pose dimension tuple in metres. Semantics
            vary per shape; see the individual shape docstrings.
    """

    shape_id: str
    rest_dimensions: tuple[float, ...]

    def vertices_at_rest(self) -> NDArray[np.floating]:
        """Return ``(V, 3)`` vertex array in the shape's local frame.

        Vertices are in the canonical rest-pose orientation defined by
        the shape's binding. The returned array is read-only.

        Postcondition: ``result.shape == (V, 3)`` for some ``V >= 1``;
        ``result.dtype.kind == 'f'``.
        """
        ...

    def faces(self) -> NDArray[np.integer]:
        """Return ``(F, 3)`` triangle index array.

        For 1-D shapes (lines), this is an empty ``(0, 3)`` array.

        Postcondition: ``result.shape[1] == 3``;
        ``result.dtype.kind in ('i', 'u')``.
        """
        ...

    def transform(self, fitted: FittedShape) -> NDArray[np.floating]:
        """Return ``(T, V, 3)`` vertices after fitting transformation.

        Args:
            fitted: Per-frame placement to apply. Must have
                ``fitted.shape_id == self.shape_id``.

        Postcondition: ``result.shape == (fitted.n_frames, V, 3)``
        where ``V == self.vertices_at_rest().shape[0]``.
        """
        ...


@runtime_checkable
class ShapeFitter(Protocol):
    """Compute a per-frame transform from markers to a fitted shape.

    Implementations: ``BetweenTwoMarkersFitter``, ``ClusterKabschFitter``,
    ``ProcrustesAnisotropicFitter`` (added in issue #4756).
    """

    def fit(
        self,
        shape: BodyPartShape,
        binding: MarkerBinding,
        markers_xyz: dict[str, NDArray[np.floating]],
    ) -> FittedShape:
        """Compute the per-frame fit.

        Args:
            shape: The shape to fit. Must satisfy the
                :class:`BodyPartShape` protocol.
            binding: Marker binding describing how the shape attaches.
                Every name in ``binding.marker_names`` must be a key of
                ``markers_xyz``.
            markers_xyz: Mapping ``marker_name -> (T, 3) ndarray``. All
                marker arrays must agree on ``T``. Missing samples are
                represented as ``nan`` and propagate to
                :attr:`FittedShape.valid_mask`.

        Returns:
            A :class:`FittedShape` whose ``shape_id`` matches
            ``shape.shape_id`` and whose array-shape invariants are
            checked at construction.

        Raises:
            ValueError: If ``binding.marker_names`` references markers
                absent from ``markers_xyz``, or if marker arrays disagree
                on the time dimension.
        """
        ...


@runtime_checkable
class ShapeRenderer(Protocol):
    """Backend-specific renderer for body-part shapes.

    Implementations live in :mod:`body_part_viz.renderers` and are added
    in issues #4760 (matplotlib) and #4762 (pyqtgraph). This contract
    intentionally exposes no Qt or matplotlib types so subclasses may
    pick up the backend lazily.
    """

    def add_shape(
        self,
        shape: BodyPartShape,
        fitted: FittedShape,
        theme: ShapeTheme,
    ) -> str:
        """Add a shape to the scene.

        Returns:
            An opaque handle string that can be passed to
            :meth:`update_frame`, :meth:`set_visible`, or :meth:`remove`.

        Raises:
            ValueError: If ``shape.shape_id != fitted.shape_id``.
        """
        ...

    def update_frame(self, handle: str, frame_idx: int) -> None:
        """Render the shape at the given frame.

        Args:
            handle: Handle returned from :meth:`add_shape`.
            frame_idx: Frame index in ``range(0, fitted.n_frames)``.

        Raises:
            KeyError: If ``handle`` is unknown.
            IndexError: If ``frame_idx`` is out of range.
        """
        ...

    def set_visible(self, handle: str, visible: bool) -> None:
        """Toggle visibility of a previously added shape.

        Raises:
            KeyError: If ``handle`` is unknown.
        """
        ...

    def remove(self, handle: str) -> None:
        """Remove a shape from the scene.

        Idempotent: removing an unknown handle is a no-op.
        """
        ...
