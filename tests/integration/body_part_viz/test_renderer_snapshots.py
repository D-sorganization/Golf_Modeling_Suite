"""Golden-hash snapshot tests for the matplotlib body_part_viz renderer.

We avoid raster pixel-diffs (notoriously flaky cross-platform) and
instead capture an md5/sha256 hash of the matplotlib canvas ARGB
buffer for each shape kind at a fixed seed and fixed parameters. The
expected hashes live in ``tests/fixtures/body_part_viz/snapshot_hashes.json``.

Authoring workflow
------------------
Run pytest with ``--update-goldens`` once to write the JSON file, then
re-run without the flag to confirm the assertions pass.

Skips
-----
The whole module is skipped if matplotlib is unavailable. Snapshots
that have no recorded golden are skipped (first-run path) unless
``--update-goldens`` is provided.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

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
from src.shared.python.body_part_viz.shapes import (  # noqa: E402
    CapsuleShape,
    CylinderShape,
    EllipsoidShape,
    LineShape,
)

GOLDEN_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "fixtures"
    / "body_part_viz"
    / "snapshot_hashes.json"
)

# Fixed RNG seed: every snapshot is built from this stream so hashes are
# deterministic across runs.
_SEED = 20260508


def _hash_bytes(data: bytes) -> str:
    """Return a short stable digest. Prefer md5; fall back to sha256."""
    try:
        return hashlib.md5(data, usedforsecurity=False).hexdigest()
    except TypeError:  # pragma: no cover - very old Python
        return hashlib.sha256(data).hexdigest()


def _identity_fitted(shape_id: str, n_frames: int = 2) -> FittedShape:
    binding = MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("a", "b"),
    )
    centroid = np.zeros((n_frames, 3))
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


def _build_figure_for(kind: str) -> Any:
    """Return a configured matplotlib Figure with a single shape rendered."""
    rng = np.random.default_rng(_SEED)
    # Ensure the matplotlib internal seed is also pinned for color cycling
    # paths that may consult ``np.random`` (defensive).
    np.random.seed(_SEED)
    _ = rng.standard_normal(4)  # touch the stream so future edits notice

    fig = plt.figure(figsize=(4.0, 4.0), dpi=72)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlim(-1.0, 2.0)
    ax.set_ylim(-1.0, 1.0)
    ax.set_zlim(-1.0, 1.0)
    ax.set_axis_off()

    theme = ShapeTheme(color="#1f77b4", opacity=0.5)
    renderer = MatplotlibRenderer(ax)

    if kind == "line":
        shape: Any = LineShape(length=1.0, shape_id="line-snap")
    elif kind == "cylinder":
        shape = CylinderShape(length=1.0, radius=0.25, n_facets=12, shape_id="cyl-snap")
    elif kind == "ellipsoid":
        shape = EllipsoidShape(
            a=0.5, b=0.3, c=0.2, n_lon=12, n_lat=6, shape_id="ell-snap"
        )
    elif kind == "capsule":
        shape = CapsuleShape(
            length=1.0,
            radius=0.2,
            n_facets=12,
            n_lat=4,
            shape_id="cap-snap",
        )
    else:  # pragma: no cover - guarded by parametrize
        raise AssertionError(f"unknown kind {kind!r}")

    handle = renderer.add_shape(shape, _identity_fitted(shape.shape_id), theme)
    renderer.update_frame(handle, 0)
    fig.canvas.draw()
    return fig


def _hash_for_kind(kind: str) -> str:
    fig = _build_figure_for(kind)
    try:
        buf = fig.canvas.tostring_argb()
    finally:
        plt.close(fig)
    return _hash_bytes(buf)


def _load_goldens() -> dict[str, str]:
    if not GOLDEN_PATH.exists():
        return {}
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _write_goldens(data: dict[str, str]) -> None:
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("kind", ["line", "cylinder", "ellipsoid", "capsule"])
def test_renderer_snapshot_hash(kind: str, update_goldens: bool) -> None:
    actual = _hash_for_kind(kind)

    goldens = _load_goldens()
    if update_goldens:
        goldens[kind] = actual
        _write_goldens(goldens)
        return

    if kind not in goldens:
        pytest.skip(
            f"no golden recorded for {kind!r}; "
            "run pytest with --update-goldens to seed it"
        )

    assert actual == goldens[kind], (
        f"renderer hash drift for shape {kind!r}: "
        f"expected {goldens[kind]}, got {actual}"
    )


def test_hash_is_stable_across_two_invocations() -> None:
    """Calling the build function twice must produce the same hash."""
    first = _hash_for_kind("cylinder")
    second = _hash_for_kind("cylinder")
    assert first == second
