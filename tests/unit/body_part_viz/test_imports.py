"""Public API import smoke test for body_part_viz.

Confirms the documented public surface is importable in one statement
and that nothing was forgotten in ``__all__``.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_public_api_imports_without_error() -> None:
    """The documented one-line import works."""
    from src.shared.python.body_part_viz import (  # noqa: F401
        BindingKind,
        BodyPartShape,
        FittedShape,
        MarkerBinding,
        ShapeFitter,
        ShapeRenderer,
        ShapeTheme,
    )


@pytest.mark.unit
def test_all_lists_every_public_export() -> None:
    """``__all__`` matches the documented public surface."""
    from src.shared.python import body_part_viz

    expected = {
        "BindingKind",
        "BodyPartShape",
        "FittedShape",
        "MarkerBinding",
        "ShapeFitter",
        "ShapeRenderer",
        "ShapeTheme",
    }
    assert set(body_part_viz.__all__) == expected


@pytest.mark.unit
def test_subpackage_placeholders_load() -> None:
    """The sub-packages import without raising.

    ``shapes`` exposes the primitive shapes added in #4759; ``fitters``
    and ``renderers`` remain placeholders pending later issues of
    EPIC #4755.
    """
    from src.shared.python.body_part_viz import (  # noqa: F401
        fitters,
        renderers,
        shapes,
    )

    assert set(shapes.__all__) == {
        "CapsuleShape",
        "CompositeShape",
        "CylinderShape",
        "EllipsoidShape",
        "LineShape",
    }
    assert fitters.__all__ == []
    assert renderers.__all__ == []
