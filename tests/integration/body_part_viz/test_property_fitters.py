"""Hypothesis property-based tests for the three body_part_viz fitters.

Properties checked
------------------
1. ``shape.transform(fit_result)`` returns ``(V, 3)`` finite vertices on
   valid frames (the contract-stated post-shape; per-frame iteration here
   builds a ``(T, V, 3)`` stack to also exercise the per-frame helper).
2. ``valid_mask`` correctly tracks NaN propagation injected into markers.
3. Idempotence on rest pose: feeding the rest-pose markers back into the
   fitter yields rotation ~ identity and unit scale on valid frames.

Hypothesis is capped at 50 examples per test so the suite remains fast
(<30 s default tier). Module is skipped if ``hypothesis`` is missing.
"""

from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis")

import numpy as np  # noqa: E402
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from src.shared.python.body_part_viz import (  # noqa: E402
    BindingKind,
    FittedShape,
    MarkerBinding,
)
from src.shared.python.body_part_viz.fitters import (  # noqa: E402
    BetweenTwoMarkersFitter,
    ClusterKabschFitter,
    ProcrustesAnisotropicFitter,
)
from src.shared.python.body_part_viz.shapes import (  # noqa: E402
    CylinderShape,
    LineShape,
)

_HYPO_SETTINGS = settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

_FINITE = st.floats(
    min_value=-10.0,
    max_value=10.0,
    allow_nan=False,
    allow_infinity=False,
    width=64,
)


def _xyz(draw: st.DrawFn) -> np.ndarray:
    return np.array(
        [draw(_FINITE), draw(_FINITE), draw(_FINITE)],
        dtype=float,
    )


@st.composite
def _between_two_markers(draw: st.DrawFn, n_frames: int = 6) -> dict[str, np.ndarray]:
    """Markers ``A`` and ``B`` with B = A + axis * length, length > 0."""
    a = np.zeros((n_frames, 3))
    b = np.zeros((n_frames, 3))
    for t in range(n_frames):
        origin = _xyz(draw)
        # Random direction (rejection sample for non-zero norm).
        for _ in range(8):
            direction = _xyz(draw)
            n = float(np.linalg.norm(direction))
            if n > 0.1:
                direction = direction / n
                break
        else:  # pragma: no cover - extremely rare with hypothesis
            direction = np.array([1.0, 0.0, 0.0])
        length = float(draw(st.floats(min_value=0.2, max_value=2.0)))
        a[t] = origin
        b[t] = origin + direction * length
    return {"A": a, "B": b}


@st.composite
def _cluster_markers(
    draw: st.DrawFn, n_markers: int = 4, n_frames: int = 5
) -> dict[str, np.ndarray]:
    """Rigid cluster: a fixed local layout rotated/translated per frame."""
    # Local layout: tetrahedron-ish, non-degenerate.
    local = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )[:n_markers]

    rng_seed = draw(st.integers(min_value=0, max_value=1_000_000))
    rng = np.random.default_rng(rng_seed)

    out: dict[str, np.ndarray] = {
        f"M{i}": np.zeros((n_frames, 3)) for i in range(n_markers)
    }
    for t in range(n_frames):
        # Random rotation via QR of a Gaussian matrix.
        a_mat = rng.standard_normal((3, 3))
        q_mat, r_mat = np.linalg.qr(a_mat)
        # Ensure det == +1 (proper rotation).
        if float(np.linalg.det(q_mat)) < 0.0:
            q_mat[:, 0] *= -1.0
        translation = np.array(
            [draw(_FINITE), draw(_FINITE), draw(_FINITE)], dtype=float
        )
        transformed = local @ q_mat.T + translation
        for i in range(n_markers):
            out[f"M{i}"][t] = transformed[i]
    return out


# ---------------------------------------------------------------------------
# BetweenTwoMarkersFitter
# ---------------------------------------------------------------------------
@given(markers=_between_two_markers())
@_HYPO_SETTINGS
def test_between_two_produces_valid_fitted_shape(
    markers: dict[str, np.ndarray],
) -> None:
    shape = LineShape(length=1.0, shape_id="line-prop")
    binding = MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("A", "B"),
        rest_dimensions=(1.0,),
    )
    fitter = BetweenTwoMarkersFitter()
    fitted = fitter.fit(shape, binding, markers)

    n_frames = markers["A"].shape[0]
    assert fitted.centroid.shape == (n_frames, 3)
    assert fitted.rotation_matrix.shape == (n_frames, 3, 3)
    assert fitted.scale.shape == (n_frames, 3)
    assert fitted.valid_mask.shape == (n_frames,)
    assert bool(fitted.valid_mask.all())

    transformed = shape.transform(fitted)
    # Cylinder/Line transform contract is (T, V, 3): one vertex set per frame.
    assert transformed.ndim == 3
    assert transformed.shape[0] == n_frames
    assert transformed.shape[2] == 3
    assert bool(np.isfinite(transformed).all())


def test_between_two_nan_propagation() -> None:
    """NaN in any marker on a frame must mark that frame invalid."""
    rng = np.random.default_rng(0)
    a = rng.standard_normal((5, 3))
    b = a + np.array([1.0, 0.0, 0.0])
    a[2, 1] = np.nan  # corrupt a single frame

    shape = LineShape(length=1.0)
    binding = MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("A", "B"),
        rest_dimensions=(1.0,),
    )
    fitted = BetweenTwoMarkersFitter().fit(shape, binding, {"A": a, "B": b})
    assert fitted.valid_mask.tolist() == [True, True, False, True, True]


def test_between_two_idempotent_at_rest() -> None:
    """Rest-pose-aligned markers yield identity rotation and unit scale."""
    n = 3
    a = np.zeros((n, 3))
    b = np.tile(np.array([1.0, 0.0, 0.0]), (n, 1))  # length-1, along +x

    shape = LineShape(length=1.0)
    binding = MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("A", "B"),
        rest_dimensions=(1.0,),
    )
    fitted = BetweenTwoMarkersFitter().fit(shape, binding, {"A": a, "B": b})
    assert np.allclose(fitted.rotation_matrix, np.eye(3))
    assert np.allclose(fitted.scale, 1.0)


# ---------------------------------------------------------------------------
# ClusterKabschFitter
# ---------------------------------------------------------------------------
@given(markers=_cluster_markers())
@_HYPO_SETTINGS
def test_cluster_kabsch_finite_outputs(markers: dict[str, np.ndarray]) -> None:
    shape = CylinderShape(length=1.0, radius=0.1, n_facets=8, shape_id="cyl-prop")
    binding = MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=tuple(sorted(markers.keys())),
    )
    fitted = ClusterKabschFitter().fit(shape, binding, markers)

    n_frames = next(iter(markers.values())).shape[0]
    assert fitted.centroid.shape == (n_frames, 3)
    assert bool(fitted.valid_mask.all())
    assert bool(np.isfinite(fitted.centroid).all())
    assert bool(np.isfinite(fitted.rotation_matrix).all())
    # Rotation matrices must be orthonormal with det ~ +1.
    rrt = fitted.rotation_matrix @ np.swapaxes(fitted.rotation_matrix, 1, 2)
    assert np.allclose(rrt, np.broadcast_to(np.eye(3), rrt.shape), atol=1e-6)
    dets = np.linalg.det(fitted.rotation_matrix)
    assert np.allclose(dets, 1.0, atol=1e-6)


def test_cluster_kabsch_nan_propagation() -> None:
    rng = np.random.default_rng(1)
    n = 4
    markers = {f"M{i}": rng.standard_normal((4, 3)) for i in range(4)}
    markers["M1"][2, 0] = np.nan

    shape = CylinderShape(length=1.0, radius=0.1, n_facets=8)
    binding = MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=tuple(sorted(markers.keys())),
    )
    fitted = ClusterKabschFitter().fit(shape, binding, markers)
    assert not bool(fitted.valid_mask[2])
    # Other frames remain valid.
    assert bool(fitted.valid_mask[0])
    assert bool(fitted.valid_mask[1])
    assert bool(fitted.valid_mask[3])


def test_cluster_kabsch_idempotent_when_rest_pose_repeated() -> None:
    """If every frame equals the rest pose, rotation == I and scale == 1."""
    rest = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    n_frames = 3
    markers = {f"M{i}": np.tile(rest[i], (n_frames, 1)) for i in range(4)}
    shape = CylinderShape(length=1.0, radius=0.1, n_facets=8)
    binding = MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=tuple(sorted(markers.keys())),
    )
    fitted = ClusterKabschFitter(enable_scale=True).fit(shape, binding, markers)
    assert np.allclose(fitted.rotation_matrix, np.eye(3), atol=1e-9)
    assert np.allclose(fitted.scale, 1.0, atol=1e-9)


# ---------------------------------------------------------------------------
# ProcrustesAnisotropicFitter
# ---------------------------------------------------------------------------
@given(markers=_cluster_markers(n_markers=4, n_frames=4))
@_HYPO_SETTINGS
def test_procrustes_anisotropic_finite_outputs(
    markers: dict[str, np.ndarray],
) -> None:
    shape = CylinderShape(length=1.0, radius=0.1, n_facets=8, shape_id="cyl-aniso")
    binding = MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=tuple(sorted(markers.keys())),
    )
    fitted = ProcrustesAnisotropicFitter().fit(shape, binding, markers)

    assert bool(fitted.valid_mask.all())
    assert bool(np.isfinite(fitted.centroid).all())
    assert bool(np.isfinite(fitted.rotation_matrix).all())
    assert bool(np.isfinite(fitted.scale).all())
    assert bool(np.all(fitted.scale > 0.0))


def test_procrustes_anisotropic_idempotent_at_rest() -> None:
    rest = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    n_frames = 2
    markers = {f"M{i}": np.tile(rest[i], (n_frames, 1)) for i in range(4)}
    shape = CylinderShape(length=1.0, radius=0.1, n_facets=8)
    binding = MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=tuple(sorted(markers.keys())),
    )
    fitted = ProcrustesAnisotropicFitter().fit(shape, binding, markers)
    assert np.allclose(fitted.rotation_matrix, np.eye(3), atol=1e-9)
    assert np.allclose(fitted.scale, 1.0, atol=1e-6)


def test_procrustes_anisotropic_nan_propagation() -> None:
    rng = np.random.default_rng(2)
    markers = {f"M{i}": rng.standard_normal((5, 3)) for i in range(4)}
    markers["M3"][1, 2] = np.nan
    markers["M0"][4, 0] = np.nan

    shape = CylinderShape(length=1.0, radius=0.1, n_facets=8)
    binding = MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=tuple(sorted(markers.keys())),
    )
    fitted = ProcrustesAnisotropicFitter().fit(shape, binding, markers)
    assert fitted.valid_mask.tolist() == [True, False, True, True, False]
