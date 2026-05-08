"""Unit tests for the ``BodyTarget`` dataclass and validation rules.

Each validation rule has one happy-path test (covered by the shared
``_make_body_target`` helper plus :func:`test_body_target_happy_path`) and one
failure case using ``pytest.raises(ValueError, match=...)`` to pin the error
message.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from src.shared.python.motion_matching.body_target import (
    BODY_TARGET_SCHEMA_VERSION,
    MAX_BODY_POSITION_NORM_M,
    BodyEvent,
    BodyTarget,
)
from src.shared.python.motion_matching.club_target import SourceProvenance


def _make_provenance() -> SourceProvenance:
    return SourceProvenance(
        filename="trial.c3d",
        format="c3d",
        subject_id="S01",
        trial_id="T01",
        sha256="0" * 64,
    )


def _make_body_target(
    *,
    n: int = 8,
    m: int = 4,
    time: np.ndarray | None = None,
    marker_xyz: np.ndarray | None = None,
    marker_names: tuple[str, ...] | None = None,
    impact_idx: int = 4,
    events: tuple[BodyEvent, ...] | None = None,
    source: SourceProvenance | None = None,
) -> BodyTarget:
    if time is None:
        time = np.linspace(0.0, 0.1, n)
    if marker_xyz is None:
        # Small finite values well under MAX_BODY_POSITION_NORM_M.
        marker_xyz = np.zeros((n, m, 3))
        marker_xyz[..., 2] = 1.0
    if marker_names is None:
        marker_names = tuple(f"M{i}" for i in range(m))
    if events is None:
        time_s = float(time.flat[impact_idx]) if time.size > impact_idx else 0.0
        events = (BodyEvent(label="impact", frame=impact_idx, time_s=time_s),)
    if source is None:
        source = _make_provenance()
    return BodyTarget(
        time=time,
        marker_xyz=marker_xyz,
        marker_names=marker_names,
        impact_idx=impact_idx,
        events=events,
        source=source,
    )


def test_constants_exposed() -> None:
    assert BODY_TARGET_SCHEMA_VERSION == 1
    assert MAX_BODY_POSITION_NORM_M == 3.0


def test_body_target_happy_path() -> None:
    target = _make_body_target()
    assert target.coordinate_frame == "z_up_right_handed"
    assert target.marker_xyz.shape == (8, 4, 3)
    assert len(target.marker_names) == 4
    assert target.impact_idx == 4


def test_body_target_immutable() -> None:
    target = _make_body_target()
    with pytest.raises(dataclasses.FrozenInstanceError):
        target.impact_idx = 99  # type: ignore[misc]


def test_validation_rejects_non_monotonic_time() -> None:
    bad_time = np.linspace(0.0, 0.1, 8)
    bad_time[5] = bad_time[4]
    with pytest.raises(ValueError, match="strictly increasing"):
        _make_body_target(time=bad_time)


def test_validation_rejects_non_zero_start_time() -> None:
    time = np.linspace(0.05, 0.15, 8)
    with pytest.raises(ValueError, match=r"time\[0\] must be 0"):
        _make_body_target(time=time)


def test_validation_rejects_non_1d_time() -> None:
    bad_time = np.zeros((8, 1))
    with pytest.raises(ValueError, match="time must be a 1-D ndarray"):
        _make_body_target(time=bad_time)


def test_validation_rejects_too_short_time() -> None:
    with pytest.raises(ValueError, match="at least 2 samples"):
        _make_body_target(
            n=1,
            time=np.array([0.0]),
            marker_xyz=np.zeros((1, 4, 3)),
            impact_idx=0,
            events=(BodyEvent(label="impact", frame=0, time_s=0.0),),
        )


def test_validation_rejects_marker_xyz_shape_mismatch() -> None:
    bad_xyz = np.zeros((8, 5, 3))  # M==5 but names give M==4
    with pytest.raises(ValueError, match=r"marker_xyz must have shape \(8, 4, 3\)"):
        _make_body_target(marker_xyz=bad_xyz)


def test_validation_rejects_too_few_markers() -> None:
    # M=2 < 3 minimum.
    with pytest.raises(ValueError, match="marker count M must be >= 3"):
        _make_body_target(
            m=2,
            marker_xyz=np.zeros((8, 2, 3)),
            marker_names=("A", "B"),
        )


def test_validation_rejects_duplicate_marker_names() -> None:
    with pytest.raises(ValueError, match="marker_names must be unique"):
        _make_body_target(marker_names=("A", "B", "C", "A"))


def test_validation_rejects_empty_marker_name() -> None:
    with pytest.raises(ValueError, match="must be non-empty"):
        _make_body_target(marker_names=("A", "B", "C", ""))


def test_validation_rejects_non_string_marker_name() -> None:
    with pytest.raises(ValueError, match="must be a string"):
        _make_body_target(marker_names=("A", "B", "C", 1))  # type: ignore[arg-type]


def test_validation_rejects_marker_names_not_tuple() -> None:
    with pytest.raises(ValueError, match="marker_names must be a tuple"):
        _make_body_target(marker_names=["A", "B", "C", "D"])  # type: ignore[arg-type]


def test_validation_rejects_excessive_position_norm() -> None:
    n, m = 8, 4
    xyz = np.zeros((n, m, 3))
    xyz[..., 2] = 1.0
    xyz[3, 1, 0] = MAX_BODY_POSITION_NORM_M + 0.5
    with pytest.raises(ValueError, match=r"\|r\| >="):
        _make_body_target(marker_xyz=xyz)


def test_validation_allows_nan_for_occluded_samples() -> None:
    # Occluded samples are permitted; a finite frame for >=50% markers exists.
    n, m = 8, 4
    xyz = np.zeros((n, m, 3))
    xyz[..., 2] = 1.0
    xyz[2, 0, :] = np.nan  # one occluded sample
    target = _make_body_target(marker_xyz=xyz)
    assert np.isnan(target.marker_xyz[2, 0, 0])


def test_validation_rejects_insufficient_finite_coverage() -> None:
    n, m = 8, 4
    # Only 1 of 4 markers ever finite => 25% coverage < 50%.
    xyz = np.full((n, m, 3), np.nan)
    xyz[:, 0, :] = 0.0
    with pytest.raises(ValueError, match="finite"):
        _make_body_target(marker_xyz=xyz)


def test_validation_rejects_impact_idx_out_of_range() -> None:
    with pytest.raises(ValueError, match=r"impact_idx must be in \[0, 8\)"):
        _make_body_target(
            impact_idx=8,
            events=(BodyEvent(label="impact", frame=0, time_s=0.0),),
        )


def test_validation_rejects_negative_impact_idx() -> None:
    with pytest.raises(ValueError, match=r"impact_idx must be in \[0, 8\)"):
        _make_body_target(
            impact_idx=-1,
            events=(BodyEvent(label="impact", frame=0, time_s=0.0),),
        )


def test_validation_rejects_event_frame_out_of_range() -> None:
    with pytest.raises(ValueError, match=r"events\[0\].frame must be in \[0, 8\)"):
        _make_body_target(
            events=(BodyEvent(label="impact", frame=99, time_s=0.05),),
        )


def test_validation_rejects_empty_event_label() -> None:
    with pytest.raises(ValueError, match="label must be a non-empty string"):
        _make_body_target(
            events=(BodyEvent(label="", frame=4, time_s=0.05),),
        )


def test_validation_rejects_duplicate_event_labels() -> None:
    with pytest.raises(ValueError, match="events labels must be unique"):
        _make_body_target(
            events=(
                BodyEvent(label="impact", frame=4, time_s=0.05),
                BodyEvent(label="impact", frame=5, time_s=0.06),
            ),
        )


def test_validation_rejects_non_bodyevent_in_events() -> None:
    with pytest.raises(ValueError, match="must be a BodyEvent"):
        _make_body_target(events=("not-an-event",))  # type: ignore[arg-type]


def test_validation_rejects_non_tuple_events() -> None:
    with pytest.raises(ValueError, match="events must be a tuple"):
        _make_body_target(
            events=[BodyEvent(label="impact", frame=4, time_s=0.05)],  # type: ignore[arg-type]
        )


def test_validation_rejects_bad_source_type() -> None:
    with pytest.raises(TypeError, match="source must be a SourceProvenance"):
        BodyTarget(
            time=np.linspace(0.0, 0.1, 8),
            marker_xyz=np.zeros((8, 4, 3)),
            marker_names=("A", "B", "C", "D"),
            impact_idx=4,
            events=(BodyEvent(label="impact", frame=4, time_s=0.05),),
            source="not-a-provenance",  # type: ignore[arg-type]
        )
