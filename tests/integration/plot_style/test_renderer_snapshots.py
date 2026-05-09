"""Golden hash snapshot tests for the plot_style matplotlib renderer.

Each combination of (built-in MarkerShape) x (ColormapId variant) is
rendered to an RGBA buffer at fixed DPI/size on the headless ``Agg``
backend, the buffer is hashed (sha256), and the hash is compared against
``tests/fixtures/plot_style/snapshot_hashes.json``.

Set ``PLOT_STYLE_REGEN_GOLDENS=1`` to overwrite the committed hashes.

Skipped cleanly if matplotlib is unavailable.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
np = pytest.importorskip("numpy")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402

from src.shared.python.plot_style import (  # noqa: E402
    ColormapId,
    DataChannel,
    DataDrivenColor,
    MarkerShape,
    MarkerStyle,
    MatplotlibMarkerRenderer,
    StaticColor,
)

SNAPSHOT_DPI = 80
SNAPSHOT_FIGSIZE = (3.0, 3.0)
N_MARKERS = 12
SEED = 4814

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "plot_style"
HASHES_PATH = FIXTURES_DIR / "snapshot_hashes.json"
REGEN = os.environ.get("PLOT_STYLE_REGEN_GOLDENS", "").strip() not in (
    "",
    "0",
    "false",
    "False",
)

# Subset that maps cleanly to matplotlib glyphs (CUSTOM_MESH excluded:
# requires a CustomMeshSpec and is exercised in unit tests).
_BUILTIN_SHAPES = [
    MarkerShape.SPHERE,
    MarkerShape.CUBE,
    MarkerShape.CROSS,
    MarkerShape.STAR,
    MarkerShape.DIAMOND,
    MarkerShape.PLUS,
    MarkerShape.POINT,
]

_COLORMAPS = [
    ColormapId.VIRIDIS,
    ColormapId.PLASMA,
    ColormapId.TURBO,
    ColormapId.COOLWARM,
    ColormapId.VELOCITY,  # semantic alias
]


def _deterministic_positions(n: int) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    pts = rng.uniform(-1.0, 1.0, size=(n, 2))
    return pts.astype(np.float64)


def _channel_values(n: int) -> np.ndarray:
    rng = np.random.default_rng(SEED + 1)
    return rng.uniform(0.0, 1.0, size=(1, n)).astype(np.float64)


def _hash_rgba(arr: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(arr, dtype=np.uint8).tobytes())
    h.update(str(arr.shape).encode("utf-8"))
    return h.hexdigest()


def _render_buffer(style: MarkerStyle) -> np.ndarray:
    fig = plt.figure(figsize=SNAPSHOT_FIGSIZE, dpi=SNAPSHOT_DPI)
    try:
        ax = fig.add_subplot(111)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_axis_off()
        renderer = MatplotlibMarkerRenderer(ax)
        positions = _deterministic_positions(N_MARKERS)
        renderer.add_markers(positions, style)
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        return buf.reshape(int(h), int(w), 4).copy()
    finally:
        plt.close(fig)


def _load_hashes() -> dict[str, str]:
    if not HASHES_PATH.is_file():
        return {}
    return json.loads(HASHES_PATH.read_text(encoding="utf-8"))


def _save_hashes(hashes: dict[str, str]) -> None:
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASHES_PATH.write_text(
        json.dumps(dict(sorted(hashes.items())), indent=2) + "\n",
        encoding="utf-8",
    )


def _compare_or_regen(key: str, digest: str) -> None:
    hashes = _load_hashes()
    if REGEN or key not in hashes:
        hashes[key] = digest
        _save_hashes(hashes)
        if not REGEN:
            pytest.skip(
                f"Generated missing golden hash for {key!r} on first run; "
                "rerun the test to compare."
            )
        return
    expected = hashes[key]
    assert digest == expected, (
        f"snapshot {key!r} sha256 mismatch: got {digest!r}, expected {expected!r}"
    )


@pytest.mark.parametrize("shape", _BUILTIN_SHAPES, ids=lambda s: s.value)
def test_shape_static_color_snapshot(shape: MarkerShape) -> None:
    """Each built-in shape with a constant fill renders to a stable hash."""
    style = MarkerStyle(
        shape=shape,
        size_px=10.0,
        edge_color="#000000",
        edge_width=0.5,
        fill_color=StaticColor("#1f77b4"),
        opacity=1.0,
    )
    buf = _render_buffer(style)
    digest = _hash_rgba(buf)
    _compare_or_regen(f"shape_static::{shape.value}", digest)


@pytest.mark.parametrize("cmap", _COLORMAPS, ids=lambda c: c.value)
def test_colormap_data_driven_snapshot(cmap: ColormapId) -> None:
    """Each colormap, sampled by a deterministic channel, renders stably."""
    channel = DataChannel(name="ch", values=_channel_values(N_MARKERS))
    style = MarkerStyle(
        shape=MarkerShape.SPHERE,
        size_px=12.0,
        edge_color="#000000",
        edge_width=0.5,
        fill_color=DataDrivenColor(channel=channel, colormap=cmap, vmin=0.0, vmax=1.0),
        opacity=1.0,
    )
    buf = _render_buffer(style)
    digest = _hash_rgba(buf)
    _compare_or_regen(f"colormap::{cmap.value}", digest)
