"""Unit tests for :class:`PaletteColorResolver`."""

from __future__ import annotations

import numpy as np
import pytest
from matplotlib import colormaps
from matplotlib.colors import to_rgba

from src.shared.python.plot_style import PaletteColor, StaticColor
from src.shared.python.plot_style.contracts import ColorResolver
from src.shared.python.plot_style.resolvers import (
    PaletteColorResolver,
    list_custom_palettes,
    register_palette,
    unregister_palette,
)


@pytest.fixture
def resolver() -> PaletteColorResolver:
    return PaletteColorResolver()


@pytest.fixture(autouse=True)
def _clean_custom_palettes():
    """Ensure each test runs against a fresh custom palette registry."""
    before = list_custom_palettes()
    yield
    # Unregister anything added during the test.
    for name in list_custom_palettes():
        if name not in before:
            unregister_palette(name)


# ---------- Protocol conformance ---------------------------------------


def test_palette_resolver_implements_protocol(
    resolver: PaletteColorResolver,
) -> None:
    assert isinstance(resolver, ColorResolver)


# ---------- index in range ----------------------------------------------


@pytest.mark.parametrize("name", ["tab10", "tab20", "Set1", "Set2", "Pastel1"])
def test_palette_in_range(name: str, resolver: PaletteColorResolver) -> None:
    scale = PaletteColor(palette_name=name, palette_index=0)
    rgba = resolver.resolve_one(scale, frame_idx=0)
    cmap = colormaps[name]
    expected = tuple(float(c) for c in cmap(0))
    assert rgba == pytest.approx(expected, abs=1e-12)


def test_palette_continuous_colormap_wraps(resolver: PaletteColorResolver) -> None:
    # viridis_r has N=256; large indices wrap modulo N rather than raise.
    scale = PaletteColor(palette_name="viridis_r", palette_index=300)
    rgba = resolver.resolve_one(scale, frame_idx=0)
    cmap = colormaps["viridis_r"]
    expected = tuple(float(c) for c in cmap(300 % 256))
    assert rgba == pytest.approx(expected, abs=1e-12)


# ---------- OOB raises with palette length ------------------------------


def test_palette_oob_lists_palette_length(resolver: PaletteColorResolver) -> None:
    # tab10 has exactly 10 entries (qualitative palette).
    scale = PaletteColor(palette_name="tab10", palette_index=42)
    with pytest.raises(ValueError, match="length 10"):
        resolver.resolve_one(scale, 0)


def test_palette_oob_message_includes_index(
    resolver: PaletteColorResolver,
) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=42)
    with pytest.raises(ValueError, match="42"):
        resolver.resolve_one(scale, 0)


# ---------- unknown palette ---------------------------------------------


def test_unknown_palette_raises_at_construction() -> None:
    """PaletteColor validates the palette name against matplotlib eagerly."""
    with pytest.raises(ValueError, match="not_a_palette"):
        PaletteColor(palette_name="definitely_not_a_palette", palette_index=0)


def test_unknown_palette_lists_available_via_resolver(
    resolver: PaletteColorResolver,
) -> None:
    """If a scale somehow carries an unknown palette, the resolver
    surfaces it with a helpful message listing available palettes.

    PaletteColor's ``__post_init__`` blocks construction of bad names,
    so we mutate a freshly built scale with ``object.__setattr__`` to
    sneak past the dataclass guard and exercise the resolver branch.
    """
    scale = PaletteColor(palette_name="tab10", palette_index=0)
    object.__setattr__(scale, "palette_name", "definitely_not_a_palette")
    with pytest.raises(ValueError, match="unknown palette"):
        resolver.resolve_one(scale, 0)


# ---------- custom palettes ---------------------------------------------


def test_register_palette_round_trip(resolver: PaletteColorResolver) -> None:
    register_palette("brand_colors", ["#ff0000", "#00ff00", "#0000ff"])
    assert "brand_colors" in list_custom_palettes()
    # PaletteColor validation will not accept "brand_colors" because it
    # is not in matplotlib.colormaps. We test the resolver's internal
    # dispatch by constructing the scale lazily — the resolver should
    # honour custom palettes via its own lookup path.
    # Use the helper directly: register a name that *also* exists in
    # matplotlib but with a custom palette that shadows it.
    register_palette("Set2", ["#111111", "#222222"])
    scale = PaletteColor(palette_name="Set2", palette_index=1)
    rgba = resolver.resolve_one(scale, 0)
    expected = tuple(float(c) for c in to_rgba("#222222"))
    assert rgba == pytest.approx(expected, abs=1e-12)


def test_register_palette_oob(resolver: PaletteColorResolver) -> None:
    register_palette("Set2", ["#111111", "#222222"])
    scale = PaletteColor(palette_name="Set2", palette_index=5)
    with pytest.raises(ValueError, match="length 2"):
        resolver.resolve_one(scale, 0)


def test_register_palette_validation() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        register_palette("", ["#ff0000"])
    with pytest.raises(ValueError, match="at least one"):
        register_palette("empty", [])
    with pytest.raises(ValueError, match="not a parseable"):
        register_palette("bad", ["#zzzzzz"])
    with pytest.raises(TypeError, match="sequence"):
        register_palette("bad", "not_a_list")  # type: ignore[arg-type]


def test_unregister_palette_no_op() -> None:
    # Should silently succeed even if name is unknown.
    unregister_palette("never_registered_palette")


# ---------- bulk path ---------------------------------------------------


def test_palette_resolve_array_2d(resolver: PaletteColorResolver) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=3)
    out = resolver.resolve_array(scale, n_frames=4, n_markers=7)
    assert out.shape == (4, 7, 4)
    expected = np.asarray(colormaps["tab10"](3), dtype=np.float64)
    np.testing.assert_allclose(out, np.broadcast_to(expected, (4, 7, 4)), atol=1e-12)


def test_palette_resolve_array_1d(resolver: PaletteColorResolver) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=2)
    out = resolver.resolve_array(scale, n_frames=10)
    assert out.shape == (10, 4)


def test_palette_resolve_array_invalid_args(
    resolver: PaletteColorResolver,
) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=0)
    with pytest.raises(ValueError, match="n_frames"):
        resolver.resolve_array(scale, n_frames=-1)
    with pytest.raises(ValueError, match="n_markers"):
        resolver.resolve_array(scale, n_frames=4, n_markers=-2)


def test_palette_resolver_rejects_wrong_scale(
    resolver: PaletteColorResolver,
) -> None:
    static = StaticColor(hex_value="#ffffff")
    with pytest.raises(TypeError, match="PaletteColorResolver"):
        resolver.resolve_one(static, 0)
    with pytest.raises(TypeError, match="PaletteColorResolver"):
        resolver.resolve_array(static, n_frames=3)


def test_palette_resolve_one_negative_index() -> None:
    # PaletteColor itself rejects negative indices; the resolver path
    # double-checks. Construct via dataclass.replace to bypass.
    scale = PaletteColor(palette_name="tab10", palette_index=0)
    object.__setattr__(scale, "palette_index", -3)  # type: ignore[misc]
    resolver = PaletteColorResolver()
    with pytest.raises(ValueError, match="non-negative"):
        resolver.resolve_one(scale, 0)
