"""Unit tests for :class:`DataDrivenColorResolver`."""

from __future__ import annotations

import time

import numpy as np
import pytest

from src.shared.python.plot_style import (
    ColormapId,
    DataChannel,
    DataDrivenColor,
    PaletteColor,
)
from src.shared.python.plot_style.contracts import ColorResolver
from src.shared.python.plot_style.resolvers import DataDrivenColorResolver


@pytest.fixture
def resolver() -> DataDrivenColorResolver:
    return DataDrivenColorResolver()


# ---------- Protocol conformance ---------------------------------------


def test_data_driven_resolver_implements_protocol(
    resolver: DataDrivenColorResolver,
) -> None:
    assert isinstance(resolver, ColorResolver)


# ---------- Single-pair resolution -------------------------------------


def test_resolve_one_finite(resolver: DataDrivenColorResolver) -> None:
    rng = np.random.default_rng(0)
    values = rng.random((20, 5)).astype(np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
    )
    rgba = resolver.resolve_one(scale, frame_idx=4, marker_idx=2)
    assert len(rgba) == 4
    for component in rgba:
        assert 0.0 <= component <= 1.0


def test_resolve_one_nan_yields_nan_color(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.array([[np.nan, 0.5], [1.0, 2.0]], dtype=np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=2.0,
        nan_color="#abcdef",
    )
    rgba = resolver.resolve_one(scale, 0, 0)
    expected = (
        0xAB / 255.0,
        0xCD / 255.0,
        0xEF / 255.0,
        1.0,
    )
    assert rgba == pytest.approx(expected, abs=1e-6)


def test_resolve_one_rejects_wrong_scale(
    resolver: DataDrivenColorResolver,
) -> None:
    scale = PaletteColor(palette_name="tab10", palette_index=0)
    with pytest.raises(TypeError, match="DataDrivenColorResolver"):
        resolver.resolve_one(scale, 0)


# ---------- Equivalence: per-frame, per-(frame,marker), bulk ----------


def test_per_frame_marker_and_bulk_paths_agree(
    resolver: DataDrivenColorResolver,
) -> None:
    rng = np.random.default_rng(42)
    n_frames, n_markers = 23, 9
    values = rng.uniform(-3.0, 5.0, size=(n_frames, n_markers))
    channel = DataChannel(name="speed", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.PLASMA,
        vmin=-3.0,
        vmax=5.0,
    )

    bulk = resolver.resolve_array(scale, n_frames, n_markers)
    assert bulk.shape == (n_frames, n_markers, 4)

    for frame in range(n_frames):
        for marker in range(n_markers):
            single = resolver.resolve_one(scale, frame, marker)
            np.testing.assert_allclose(bulk[frame, marker], single, atol=1e-12)


def test_per_frame_path_matches_bulk_1d(
    resolver: DataDrivenColorResolver,
) -> None:
    rng = np.random.default_rng(7)
    n_frames = 30
    values = rng.uniform(0.0, 10.0, size=n_frames)
    channel = DataChannel(name="height", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.HEIGHT,
        vmin=0.0,
        vmax=10.0,
    )

    bulk = resolver.resolve_array(scale, n_frames)
    assert bulk.shape == (n_frames, 4)
    for frame in range(n_frames):
        single = resolver.resolve_one(scale, frame, None)
        np.testing.assert_allclose(bulk[frame], single, atol=1e-12)


# ---------- NaN handling on bulk path ----------------------------------


def test_bulk_nan_values_yield_nan_color(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.array(
        [
            [0.0, 1.0, np.nan],
            [np.nan, 0.5, 0.25],
        ],
        dtype=np.float64,
    )
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
        nan_color="#ff00ff",
    )
    bulk = resolver.resolve_array(scale, n_frames=2, n_markers=3)
    nan_expected = np.array([1.0, 0.0, 1.0, 1.0])
    np.testing.assert_allclose(bulk[0, 2], nan_expected, atol=1e-6)
    np.testing.assert_allclose(bulk[1, 0], nan_expected, atol=1e-6)
    # Finite values must NOT be the NaN color.
    assert not np.allclose(bulk[0, 0], nan_expected, atol=1e-6)


# ---------- Auto vmin / vmax -------------------------------------------


def test_auto_range_vmin_vmax_none(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.array([[2.0, 4.0, 6.0], [3.0, 5.0, 7.0]], dtype=np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=None,
        vmax=None,
    )

    bulk = resolver.resolve_array(scale, 2, 3)
    # The minimum value (2.0) maps to colormap[0]; the maximum (7.0)
    # maps to colormap[N-1]. Both must equal the LUT endpoints to within
    # the LUT-quantisation tolerance.
    from matplotlib import colormaps

    cmap = colormaps["viridis"]
    expected_min = np.asarray(cmap(0.0), dtype=np.float64)
    expected_max = np.asarray(cmap(1.0), dtype=np.float64)
    np.testing.assert_allclose(bulk[0, 0], expected_min, atol=1e-2)
    np.testing.assert_allclose(bulk[1, 2], expected_max, atol=1e-2)


# ---------- Degenerate vmin == vmax -----------------------------------


def test_vmin_equals_vmax_maps_to_midpoint(
    resolver: DataDrivenColorResolver,
) -> None:
    # vmin == vmax forbidden by DataDrivenColor.__post_init__, so we
    # build the scale, then mutate to force the degenerate case.
    values = np.array([[1.0, 1.0, 1.0]], dtype=np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
    )
    object.__setattr__(scale, "vmin", 1.0)
    object.__setattr__(scale, "vmax", 1.0)

    bulk = resolver.resolve_array(scale, 1, 3)
    from matplotlib import colormaps

    cmap = colormaps["viridis"]
    expected = np.asarray(cmap(0.5), dtype=np.float64)
    for marker in range(3):
        np.testing.assert_allclose(bulk[0, marker], expected, atol=1e-2)

    # And the single-pair path should agree.
    single = resolver.resolve_one(scale, 0, 0)
    np.testing.assert_allclose(np.asarray(single), expected, atol=1e-2)


# ---------- No usable bounds -------------------------------------------


def test_all_nan_channel_yields_nan_color(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.full((3, 4), np.nan, dtype=np.float64)
    channel = DataChannel(name="empty", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=None,
        vmax=None,
        nan_color="#ff0000",
    )
    bulk = resolver.resolve_array(scale, 3, 4)
    nan_rgba = np.array([1.0, 0.0, 0.0, 1.0])
    for frame in range(3):
        for marker in range(4):
            np.testing.assert_allclose(bulk[frame, marker], nan_rgba, atol=1e-6)


# ---------- Bulk shapes -------------------------------------------------


def test_bulk_1d_channel_with_n_markers_broadcasts(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.linspace(0.0, 1.0, 10, dtype=np.float64)
    channel = DataChannel(name="height", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
    )
    bulk = resolver.resolve_array(scale, n_frames=10, n_markers=4)
    assert bulk.shape == (10, 4, 4)
    # Within a frame, every marker shares the same color.
    for frame in range(10):
        for marker in range(1, 4):
            np.testing.assert_allclose(bulk[frame, marker], bulk[frame, 0], atol=1e-12)


def test_bulk_2d_channel_no_n_markers_uses_mean(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.array([[0.0, 1.0], [0.5, 0.5]], dtype=np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
    )
    bulk = resolver.resolve_array(scale, n_frames=2)
    assert bulk.shape == (2, 4)
    # Both rows have mean 0.5 → identical color.
    np.testing.assert_allclose(bulk[0], bulk[1], atol=1e-12)


def test_bulk_oversized_frames_padded_with_nan_color(
    resolver: DataDrivenColorResolver,
) -> None:
    values = np.array([0.0, 1.0], dtype=np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
        nan_color="#ff00ff",
    )
    bulk = resolver.resolve_array(scale, n_frames=5)
    nan_rgba = np.array([1.0, 0.0, 1.0, 1.0])
    for frame in range(2, 5):
        np.testing.assert_allclose(bulk[frame], nan_rgba, atol=1e-6)


def test_bulk_invalid_args(resolver: DataDrivenColorResolver) -> None:
    values = np.array([0.0, 1.0], dtype=np.float64)
    channel = DataChannel(name="x", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VIRIDIS,
        vmin=0.0,
        vmax=1.0,
    )
    with pytest.raises(ValueError, match="n_frames"):
        resolver.resolve_array(scale, n_frames=0)
    with pytest.raises(ValueError, match="n_markers"):
        resolver.resolve_array(scale, n_frames=2, n_markers=0)
    from src.shared.python.plot_style import StaticColor

    with pytest.raises(TypeError, match="DataDrivenColorResolver"):
        resolver.resolve_array(StaticColor(hex_value="#ffffff"), n_frames=4)


def test_lut_size_validation() -> None:
    with pytest.raises(ValueError, match="lut_size"):
        DataDrivenColorResolver(lut_size=1)
    with pytest.raises(ValueError, match="lut_size"):
        DataDrivenColorResolver(lut_size=-3)


# ---------- Performance contract ---------------------------------------


@pytest.mark.benchmark
def test_bulk_perf_38_markers_654_frames(
    resolver: DataDrivenColorResolver,
) -> None:
    """Bulk LUT must complete in ≤ 5 ms for the 38×654 target."""
    n_frames, n_markers = 654, 38
    rng = np.random.default_rng(2026)
    values = rng.uniform(0.0, 10.0, size=(n_frames, n_markers))
    channel = DataChannel(name="speed", values=values)
    scale = DataDrivenColor(
        channel=channel,
        colormap=ColormapId.VELOCITY,
        vmin=0.0,
        vmax=10.0,
    )

    # Warm caches (LUT first build).
    _ = resolver.resolve_array(scale, n_frames, n_markers)

    # Best-of-5 to absorb noise.
    runs = []
    for _ in range(5):
        start = time.perf_counter()
        out = resolver.resolve_array(scale, n_frames, n_markers)
        runs.append(time.perf_counter() - start)
    elapsed_ms = min(runs) * 1000.0
    assert out.shape == (n_frames, n_markers, 4)
    assert elapsed_ms <= 5.0, (
        f"bulk LUT took {elapsed_ms:.3f} ms, budget is 5.0 ms (≥ 60 fps)"
    )
