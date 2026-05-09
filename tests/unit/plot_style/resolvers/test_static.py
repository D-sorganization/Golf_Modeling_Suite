"""Unit tests for :class:`StaticColorResolver`."""

from __future__ import annotations

import numpy as np
import pytest
from matplotlib.colors import to_rgba

from src.shared.python.plot_style import PaletteColor, StaticColor
from src.shared.python.plot_style.contracts import ColorResolver
from src.shared.python.plot_style.resolvers import StaticColorResolver


@pytest.fixture
def resolver() -> StaticColorResolver:
    return StaticColorResolver()


# ---------- Protocol conformance ---------------------------------------


def test_static_resolver_implements_protocol(resolver: StaticColorResolver) -> None:
    assert isinstance(resolver, ColorResolver)


# ---------- resolve_one --------------------------------------------------


def test_static_resolve_one_round_trip(resolver: StaticColorResolver) -> None:
    scale = StaticColor(hex_value="#ff0000")
    rgba = resolver.resolve_one(scale, frame_idx=0, marker_idx=None)
    expected = tuple(float(c) for c in to_rgba("#ff0000"))
    assert rgba == pytest.approx(expected, abs=1e-12)


def test_static_resolve_one_named_color(resolver: StaticColorResolver) -> None:
    scale = StaticColor(hex_value="blue")
    rgba = resolver.resolve_one(scale, 5, 3)
    assert rgba[2] == pytest.approx(1.0)
    assert rgba[3] == pytest.approx(1.0)


def test_static_resolve_one_ignores_indices(resolver: StaticColorResolver) -> None:
    scale = StaticColor(hex_value="#abcdef")
    a = resolver.resolve_one(scale, 0)
    b = resolver.resolve_one(scale, 999, 17)
    assert a == b


def test_static_resolve_one_rejects_wrong_scale(
    resolver: StaticColorResolver,
) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=0)
    with pytest.raises(TypeError, match="StaticColorResolver"):
        resolver.resolve_one(scale, 0)


# ---------- bad hex ------------------------------------------------------


def test_static_color_bad_hex_construct_lists_bad_string() -> None:
    # The dataclass itself validates hex_value, so the bad-hex error
    # must surface there with the offending value mentioned.
    bad = "#zzzzzz"
    with pytest.raises(ValueError, match="zzzzzz"):
        StaticColor(hex_value=bad)


def test_static_resolver_handles_alpha_hex(resolver: StaticColorResolver) -> None:
    scale = StaticColor(hex_value="#ff000080")
    rgba = resolver.resolve_one(scale, 0)
    assert rgba[0] == pytest.approx(1.0)
    assert rgba[3] < 1.0


# ---------- resolve_array ------------------------------------------------


def test_static_resolve_array_1d(resolver: StaticColorResolver) -> None:
    scale = StaticColor(hex_value="#00ff00")
    out = resolver.resolve_array(scale, n_frames=10)
    assert out.shape == (10, 4)
    expected = np.asarray(to_rgba("#00ff00"), dtype=np.float64)
    np.testing.assert_allclose(out, np.broadcast_to(expected, (10, 4)), atol=1e-12)


def test_static_resolve_array_2d(resolver: StaticColorResolver) -> None:
    scale = StaticColor(hex_value="#0000ff")
    out = resolver.resolve_array(scale, n_frames=4, n_markers=7)
    assert out.shape == (4, 7, 4)
    expected = np.asarray(to_rgba("#0000ff"), dtype=np.float64)
    np.testing.assert_allclose(out, np.broadcast_to(expected, (4, 7, 4)), atol=1e-12)


def test_static_resolve_array_independent_of_caller_mutation(
    resolver: StaticColorResolver,
) -> None:
    scale = StaticColor(hex_value="#123456")
    a = resolver.resolve_array(scale, 5, 3)
    a[0, 0, 0] = 0.0
    b = resolver.resolve_array(scale, 5, 3)
    assert b[0, 0, 0] != 0.0


def test_static_resolve_array_invalid_n_frames(
    resolver: StaticColorResolver,
) -> None:
    scale = StaticColor(hex_value="red")
    with pytest.raises(ValueError, match="n_frames"):
        resolver.resolve_array(scale, n_frames=0)
    with pytest.raises(ValueError, match="n_frames"):
        resolver.resolve_array(scale, n_frames=-1)


def test_static_resolve_array_invalid_n_markers(
    resolver: StaticColorResolver,
) -> None:
    scale = StaticColor(hex_value="red")
    with pytest.raises(ValueError, match="n_markers"):
        resolver.resolve_array(scale, n_frames=4, n_markers=0)


def test_static_resolve_array_rejects_wrong_scale(
    resolver: StaticColorResolver,
) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=0)
    with pytest.raises(TypeError, match="StaticColorResolver"):
        resolver.resolve_array(scale, n_frames=4)
