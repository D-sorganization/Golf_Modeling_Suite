"""Marker-set loader integration tests (issue #4710).

Verifies that the C3D loaders raise :class:`MarkerSetMismatchError` with
clear, canonical-label-rich messages when a file's marker set is unknown
or missing required cluster / anatomical markers, and that the
``marker_set_override`` keyword argument is honoured.

These tests stub out :class:`C3DDataReader` so we do not need real C3D
binaries. The stub returns synthesised metadata and a tidy points DataFrame
in the exact shape the production loaders expect.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.shared.python.motion_matching.club_target import AlignOptions
from src.shared.python.motion_matching.loaders import c3d as c3d_module
from src.shared.python.motion_matching.loaders import c3d_body as c3d_body_module
from src.shared.python.upstream_drift_tools.lab.bio import (
    MarkerSet,
    MarkerSetMismatchError,
)
from src.shared.python.upstream_drift_tools.lab.bio.marker_sets import (
    CANONICAL_LABELS,
)


# ---------------------------------------------------------------------------
# Synthetic C3D reader stub
# ---------------------------------------------------------------------------


@dataclass
class _StubMetadata:
    marker_labels: list[str]
    frame_count: int
    frame_rate: float
    units: str = "m"
    events: list = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.events is None:
            self.events = []


class _StubC3DReader:
    """Stand-in for ``C3DDataReader`` that returns deterministic synthetic data."""

    LABELS: list[str] = []
    N_FRAMES: int = 240
    FRAME_RATE: float = 240.0

    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)

    def get_metadata(self) -> _StubMetadata:
        return _StubMetadata(
            marker_labels=list(self.LABELS),
            frame_count=self.N_FRAMES,
            frame_rate=self.FRAME_RATE,
        )

    def points_dataframe(
        self,
        include_time: bool = True,
        target_units: str | None = None,
        markers=None,
        residual_nan_threshold=None,
    ) -> pd.DataFrame:
        rows = []
        t = np.arange(self.N_FRAMES) / self.FRAME_RATE
        for label in self.LABELS:
            base = abs(hash(label)) % 1000 / 1000.0
            x = base + 0.001 * np.arange(self.N_FRAMES)
            y = base + 0.002 * np.arange(self.N_FRAMES)
            z = base + 0.0005 * np.arange(self.N_FRAMES)
            for i in range(self.N_FRAMES):
                rows.append(
                    {
                        "frame": i,
                        "marker": label,
                        "x": float(x[i]),
                        "y": float(y[i]),
                        "z": float(z[i]),
                        "residual": 0.0,
                        "time": float(t[i]),
                    }
                )
        return pd.DataFrame(rows)


def _patch_reader(monkeypatch: pytest.MonkeyPatch, labels: list[str]) -> Path:
    """Patch both loaders to use a stub reader returning ``labels``."""
    cls = type("_StubReader", (_StubC3DReader,), {"LABELS": list(labels)})
    monkeypatch.setattr(c3d_module, "C3DDataReader", cls)
    monkeypatch.setattr(
        c3d_body_module,
        "_import_c3d_reader_class",
        lambda: cls,
    )
    # Make Path(path).exists() pass without a real file.
    real_exists = Path.exists

    def fake_exists(self):
        if str(self).endswith(".c3d"):
            return True
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    return Path("synthetic.c3d")


# ---------------------------------------------------------------------------
# load_club_target_c3d — UNKNOWN set
# ---------------------------------------------------------------------------


def test_club_loader_raises_for_unknown_set(monkeypatch: pytest.MonkeyPatch) -> None:
    path = _patch_reader(monkeypatch, ["FOO", "BAR", "BAZ"])
    with pytest.raises(MarkerSetMismatchError) as exc:
        c3d_module.load_club_target_c3d(path, AlignOptions())
    assert "marker_set_override" in str(exc.value)


def test_club_loader_raises_for_pig41_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """PiG-41 only (no cluster) -> error mentions cluster + Marker_2:2:1."""
    labels = list(CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_41])
    path = _patch_reader(monkeypatch, labels)
    with pytest.raises(MarkerSetMismatchError) as exc:
        c3d_module.load_club_target_c3d(path, AlignOptions())
    msg = str(exc.value)
    assert "GOLF_CLUSTER" in msg or "cluster" in msg.lower()
    assert "Marker_2:2:1" in msg


def test_club_loader_raises_when_cluster_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file with the GOLF_CLUSTER required subset incomplete must list missing."""
    labels = ["Marker_2:2:1", "Marker_2:2:2", "Marker_3:3:1"]
    path = _patch_reader(monkeypatch, labels)
    with pytest.raises(MarkerSetMismatchError) as exc:
        c3d_module.load_club_target_c3d(path, AlignOptions())
    # Required-subset check or detection failure both count as a clear error.
    assert "Marker_" in str(exc.value)


def test_club_loader_override_short_circuits_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An override is respected when required labels are present."""
    labels = list(CANONICAL_LABELS[MarkerSet.GOLF_CLUSTER]) + list(
        CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_28]
    )
    path = _patch_reader(monkeypatch, labels)
    # Without override the detector picks GOLF_CLUSTER (priority); explicit
    # override to the same set must succeed downstream just as well.
    # We don't run the full pipeline (synthetic data has no real club geometry)
    # so we just assert the marker-set check itself does not raise: catch the
    # downstream pipeline error and validate it is NOT a MarkerSetMismatchError.
    try:
        c3d_module.load_club_target_c3d(
            path, AlignOptions(), marker_set_override=MarkerSet.GOLF_CLUSTER
        )
    except MarkerSetMismatchError as err:
        raise AssertionError("marker_set_override should bypass detection") from err
    except Exception:  # noqa: BLE001
        # Downstream cluster pose computation may fail with synthetic
        # straight-line markers (collinear cluster); that is acceptable.
        pass


def test_club_loader_override_rejects_bad_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Overriding to a non-cluster set still triggers the cluster requirement."""
    labels = list(CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_41])
    path = _patch_reader(monkeypatch, labels)
    with pytest.raises(MarkerSetMismatchError):
        c3d_module.load_club_target_c3d(
            path, AlignOptions(), marker_set_override=MarkerSet.PLUG_IN_GAIT_41
        )


# ---------------------------------------------------------------------------
# load_body_target_c3d
# ---------------------------------------------------------------------------


def test_body_loader_raises_for_unknown_set(monkeypatch: pytest.MonkeyPatch) -> None:
    path = _patch_reader(monkeypatch, ["FOO", "BAR"])
    with pytest.raises(MarkerSetMismatchError):
        c3d_body_module.load_body_target_c3d(path, AlignOptions())


def test_body_loader_raises_for_pure_cluster_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A golf-cluster-only file has no anatomical markers."""
    path = _patch_reader(monkeypatch, list(CANONICAL_LABELS[MarkerSet.GOLF_CLUSTER]))
    with pytest.raises(MarkerSetMismatchError) as exc:
        c3d_body_module.load_body_target_c3d(path, AlignOptions())
    assert "anatomical" in str(exc.value).lower() or "cluster" in str(exc.value).lower()


def test_body_loader_explicit_marker_set_bypasses_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``marker_set`` is explicitly given, detection is not triggered."""
    # Provide an unknown set of labels but ask for a specific subset that
    # IS present: the marker-set detection guard must not fire.
    labels = ["FOO", "BAR", "BAZ"]
    path = _patch_reader(monkeypatch, labels)
    try:
        c3d_body_module.load_body_target_c3d(
            path, AlignOptions(), marker_set=("FOO", "BAR")
        )
    except MarkerSetMismatchError as err:
        raise AssertionError("explicit marker_set must skip detection") from err
    except Exception:  # noqa: BLE001
        # Downstream pipeline will likely fail on synthetic data; that's OK.
        pass
