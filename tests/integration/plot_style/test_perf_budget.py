"""Performance budget regression for the plot_style matplotlib renderer.

100-marker scene must update at >= 30 fps mean (33 ms / frame).

Skipped if matplotlib is unavailable. Marked ``slow`` so it does not run
in default fast CI.
"""

from __future__ import annotations

import os
import time

import pytest

matplotlib = pytest.importorskip("matplotlib")
np = pytest.importorskip("numpy")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402

from src.shared.python.plot_style import (  # noqa: E402
    MarkerShape,
    MarkerStyle,
    MatplotlibMarkerRenderer,
    StaticColor,
)

N_MARKERS = 100
N_FRAMES = 60
SCALE = float(os.environ.get("PLOT_STYLE_PERF_BUDGET_SCALE", "1.0"))
BUDGET_MS = 33.0 * SCALE  # 30 fps
SEED = 4814


def _trajectory(n_markers: int, n_frames: int) -> np.ndarray:
    """Deterministic ``(T, M, 2)`` trajectory."""
    rng = np.random.default_rng(SEED)
    base = rng.uniform(-1.0, 1.0, size=(n_markers, 2))
    t = np.linspace(0.0, 2.0 * np.pi, n_frames)
    out = np.empty((n_frames, n_markers, 2), dtype=np.float64)
    for f in range(n_frames):
        out[f, :, 0] = base[:, 0] + 0.05 * np.cos(t[f])
        out[f, :, 1] = base[:, 1] + 0.05 * np.sin(t[f])
    return out


@pytest.mark.slow
@pytest.mark.benchmark
def test_perf_100_markers_30fps() -> None:
    fig = plt.figure(figsize=(3.0, 3.0), dpi=80)
    try:
        ax = fig.add_subplot(111)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        renderer = MatplotlibMarkerRenderer(ax)
        style = MarkerStyle(
            shape=MarkerShape.SPHERE,
            size_px=6.0,
            fill_color=StaticColor("#1f77b4"),
        )
        positions = _trajectory(N_MARKERS, N_FRAMES)
        handle = renderer.add_markers(positions, style)

        # Warm-up.
        for _ in range(3):
            renderer.update_frame(handle, 0)

        start = time.perf_counter()
        for f in range(N_FRAMES):
            renderer.update_frame(handle, f)
        elapsed = time.perf_counter() - start
        mean_ms = (elapsed / N_FRAMES) * 1000.0

        assert mean_ms <= BUDGET_MS, (
            f"100 markers mean per-frame {mean_ms:.2f} ms exceeds "
            f"{BUDGET_MS:.2f} ms budget (30 fps)"
        )
    finally:
        plt.close(fig)
