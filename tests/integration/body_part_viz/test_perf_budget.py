"""26-segment full-body performance budget for the matplotlib renderer.

Builds 26 cylinder shapes (humanoid segment count), feeds each an
identity ``FittedShape`` with 100 frames, and times one round of
``update_frame`` calls across all of them. The 30 fps budget allows
``26 * (1/30) s`` ~= 33 ms per frame; we assert the median across a
small sample of frames stays within that.

Marked ``slow`` so default test runs (`-m "not slow"`) skip it.
"""

from __future__ import annotations

import os
import statistics
import time

import pytest

matplotlib = pytest.importorskip("matplotlib")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src.shared.python.body_part_viz import (  # noqa: E402
    BindingKind,
    FittedShape,
    MarkerBinding,
    ShapeTheme,
)
from src.shared.python.body_part_viz.renderers import MatplotlibRenderer  # noqa: E402
from src.shared.python.body_part_viz.shapes import CylinderShape  # noqa: E402

N_SEGMENTS = 26
N_FRAMES = 100
BUDGET_MS_PER_FRAME = 33.0  # 30 fps for whole-body update


def _identity_fitted(shape_id: str, n_frames: int) -> FittedShape:
    binding = MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("a", "b"),
    )
    centroid = np.zeros((n_frames, 3))
    centroid[:, 0] = np.linspace(0.0, 1.0, n_frames)
    rotation = np.broadcast_to(np.eye(3), (n_frames, 3, 3)).copy()
    scale = np.ones((n_frames, 3))
    mask = np.ones((n_frames,), dtype=bool)
    return FittedShape(
        shape_id=shape_id,
        binding=binding,
        centroid=centroid,
        rotation_matrix=rotation,
        scale=scale,
        valid_mask=mask,
    )


@pytest.mark.slow
def test_full_body_30fps_budget() -> None:
    fig = plt.figure(figsize=(4.0, 4.0), dpi=72)
    try:
        ax = fig.add_subplot(111, projection="3d")
        ax.set_axis_off()
        renderer = MatplotlibRenderer(ax)
        theme = ShapeTheme(color="#1f77b4", opacity=0.5)

        handles: list[str] = []
        for i in range(N_SEGMENTS):
            shape = CylinderShape(
                length=0.4,
                radius=0.05,
                n_facets=10,
                shape_id=f"seg-{i:02d}",
            )
            fitted = _identity_fitted(shape.shape_id, N_FRAMES)
            handles.append(renderer.add_shape(shape, fitted, theme))

        # Warm-up to amortise first-call costs.
        for h in handles:
            renderer.update_frame(h, 0)

        # Sample a handful of frames and take the median per-frame total to
        # damp scheduling jitter.
        sampled_frames = [10, 25, 40, 55, 70, 85]
        per_frame_ms: list[float] = []
        for f in sampled_frames:
            start = time.perf_counter()
            for h in handles:
                renderer.update_frame(h, f)
            per_frame_ms.append((time.perf_counter() - start) * 1000.0)

        median_ms = statistics.median(per_frame_ms)
        assert median_ms <= BUDGET_MS_PER_FRAME, (
            f"26-segment update_frame median {median_ms:.2f} ms exceeds "
            f"30 fps budget of {BUDGET_MS_PER_FRAME:.1f} ms; "
            f"samples={[f'{x:.2f}' for x in per_frame_ms]}"
        )
    finally:
        plt.close(fig)
