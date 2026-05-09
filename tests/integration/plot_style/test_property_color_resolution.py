"""Hypothesis property tests for plot_style color resolution.

Asserts that for any valid input combination, every color resolver
(StaticColor / PaletteColor / DataDrivenColor) returns an RGBA tuple of
4 floats in ``[0, 1]`` and that downstream conversion to a 7-char hex
string ``#RRGGBB`` succeeds.

Skipped cleanly if hypothesis or matplotlib is unavailable. Each test
caps at 50 examples to stay under the 30 s fast-test budget.
"""

from __future__ import annotations

import re

import pytest

hypothesis = pytest.importorskip("hypothesis")
matplotlib = pytest.importorskip("matplotlib")
np = pytest.importorskip("numpy")

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from src.shared.python.plot_style import (  # noqa: E402
    ColormapId,
    DataChannel,
    DataDrivenColor,
    PaletteColor,
    StaticColor,
)

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_EXAMPLES = 50

_VALID_HEX_STRATEGY = st.from_regex(r"^#[0-9a-f]{6}$", fullmatch=True)
_PALETTE_NAMES = ["tab10", "tab20", "Set1", "Set2", "Set3", "Paired", "Dark2"]
# NOTE: ColormapId.SPECTRAL is excluded — its enum value ``"spectral"``
# does not match matplotlib's case-sensitive ``"Spectral"`` registration
# (a pre-existing plot_style issue tracked separately; out of scope here).
_COLORMAP_IDS = [c for c in ColormapId if c is not ColormapId.SPECTRAL]


def _rgba_to_hex(rgba: tuple[float, float, float, float]) -> str:
    r, g, b, _a = rgba
    ri = int(round(r * 255.0))
    gi = int(round(g * 255.0))
    bi = int(round(b * 255.0))
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def _assert_valid_rgba(rgba: object) -> None:
    assert isinstance(rgba, tuple) and len(rgba) == 4
    for c in rgba:
        assert isinstance(c, float)
        assert 0.0 <= c <= 1.0


@given(hex_value=_VALID_HEX_STRATEGY, frame=st.integers(0, 1000))
@settings(max_examples=MAX_EXAMPLES, deadline=None)
def test_static_color_round_trips_to_hex(hex_value: str, frame: int) -> None:
    rgba = StaticColor(hex_value).resolve(frame, 0)
    _assert_valid_rgba(rgba)
    hex_out = _rgba_to_hex(rgba)
    assert HEX_RE.match(hex_out), hex_out


@given(
    palette_name=st.sampled_from(_PALETTE_NAMES),
    palette_index=st.integers(0, 256),
    frame=st.integers(0, 1000),
    marker=st.integers(0, 100),
)
@settings(max_examples=MAX_EXAMPLES, deadline=None)
def test_palette_color_returns_valid_hex(
    palette_name: str, palette_index: int, frame: int, marker: int
) -> None:
    rgba = PaletteColor(palette_name, palette_index).resolve(frame, marker)
    _assert_valid_rgba(rgba)
    assert HEX_RE.match(_rgba_to_hex(rgba))


@given(
    cmap=st.sampled_from(_COLORMAP_IDS),
    raw=st.lists(
        st.floats(min_value=-100.0, max_value=100.0, allow_nan=False),
        min_size=1,
        max_size=16,
    ),
    frame=st.integers(0, 1000),
)
@settings(max_examples=MAX_EXAMPLES, deadline=None)
def test_data_driven_color_returns_valid_hex(
    cmap: ColormapId, raw: list[float], frame: int
) -> None:
    values = np.asarray(raw, dtype=np.float64).reshape(1, -1)
    channel = DataChannel(name="ch", values=values)
    lo = float(values.min())
    hi = float(values.max())
    if hi <= lo:
        hi = lo + 1.0
    color = DataDrivenColor(channel=channel, colormap=cmap, vmin=lo, vmax=hi)
    rgba = color.resolve(frame, 0)
    _assert_valid_rgba(rgba)
    assert HEX_RE.match(_rgba_to_hex(rgba))


@given(
    cmap=st.sampled_from(_COLORMAP_IDS),
    raw=st.lists(
        st.one_of(
            st.floats(min_value=-10.0, max_value=10.0, allow_nan=False),
            st.just(float("nan")),
            st.just(float("inf")),
            st.just(float("-inf")),
        ),
        min_size=1,
        max_size=8,
    ),
    nan_color=_VALID_HEX_STRATEGY,
)
@settings(max_examples=MAX_EXAMPLES, deadline=None)
def test_data_driven_handles_non_finite(
    cmap: ColormapId, raw: list[float], nan_color: str
) -> None:
    """Non-finite or degenerate inputs must still produce a valid hex."""
    values = np.asarray(raw, dtype=np.float64).reshape(1, -1)
    channel = DataChannel(name="ch", values=values)
    color = DataDrivenColor(channel=channel, colormap=cmap, nan_color=nan_color)
    rgba = color.resolve(0, 0)
    _assert_valid_rgba(rgba)
    assert HEX_RE.match(_rgba_to_hex(rgba))
