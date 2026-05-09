"""Pure-function tests for ``upstream_drift_tools.lab.bio.marker_sets``.

These tests cover the deterministic priority-order detector and the
``missing_required`` helper. No I/O, no fixtures.
"""

from __future__ import annotations

import logging

import pytest
from src.shared.python.upstream_drift_tools.lab.bio.marker_sets import (
    CANONICAL_LABELS,
    DETECTION_PRIORITY,
    REQUIRED_LABELS,
    MarkerSet,
    detect_marker_set,
    missing_required,
)


def test_enum_has_required_members() -> None:
    """Issue #4710 acceptance criteria: enum must include these members."""
    expected = {
        "CGM2_4",
        "PLUG_IN_GAIT_41",
        "PLUG_IN_GAIT_28",
        "IOR",
        "GOLF_CLUSTER",
        "UNKNOWN",
    }
    actual = {m.name for m in MarkerSet}
    assert expected.issubset(actual), f"Missing enum members: {expected - actual}"


def test_detection_priority_lists_each_known_set() -> None:
    known = set(MarkerSet) - {MarkerSet.UNKNOWN}
    assert set(DETECTION_PRIORITY) == known
    # No duplicates -> deterministic.
    assert len(set(DETECTION_PRIORITY)) == len(DETECTION_PRIORITY)


def test_required_subset_of_canonical() -> None:
    """Required labels must be a subset of canonical labels for every set."""
    for ms in DETECTION_PRIORITY:
        assert REQUIRED_LABELS[ms].issubset(CANONICAL_LABELS[ms]), ms.name


def test_empty_list_returns_unknown(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    assert detect_marker_set([]) is MarkerSet.UNKNOWN


def test_detect_golf_cluster() -> None:
    labels = list(CANONICAL_LABELS[MarkerSet.GOLF_CLUSTER])
    assert detect_marker_set(labels) is MarkerSet.GOLF_CLUSTER


def test_detect_plug_in_gait_41() -> None:
    labels = list(CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_41])
    assert detect_marker_set(labels) is MarkerSet.PLUG_IN_GAIT_41


def test_detect_plug_in_gait_28() -> None:
    labels = list(CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_28])
    assert detect_marker_set(labels) is MarkerSet.PLUG_IN_GAIT_28


def test_detect_cgm2_4() -> None:
    labels = list(CANONICAL_LABELS[MarkerSet.CGM2_4])
    assert detect_marker_set(labels) is MarkerSet.CGM2_4


def test_detect_ior() -> None:
    labels = list(CANONICAL_LABELS[MarkerSet.IOR])
    assert detect_marker_set(labels) is MarkerSet.IOR


def test_partial_unknown_below_threshold() -> None:
    """A handful of generic labels should not match any set."""
    assert detect_marker_set(["FOO", "BAR", "HEAD", "BUTT"]) is MarkerSet.UNKNOWN


def test_partial_pig_below_required_threshold() -> None:
    """PiG-41 with only a few labels (no full required subset) -> UNKNOWN."""
    partial = ["LFHD", "RFHD", "C7"]  # well below required count
    assert detect_marker_set(partial) is MarkerSet.UNKNOWN


def test_priority_golf_cluster_beats_pig28_when_both_present() -> None:
    """If both sets are fully present, GOLF_CLUSTER wins by priority."""
    labels = list(
        CANONICAL_LABELS[MarkerSet.GOLF_CLUSTER]
        | CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_28]
    )
    assert detect_marker_set(labels) is MarkerSet.GOLF_CLUSTER


def test_priority_cgm2_4_beats_pig41_when_both_required_present() -> None:
    """CGM2.4 has unique LTHI1..4 / RTIB1..4 markers — must win over PiG-41."""
    labels = list(
        CANONICAL_LABELS[MarkerSet.CGM2_4] | CANONICAL_LABELS[MarkerSet.PLUG_IN_GAIT_41]
    )
    assert detect_marker_set(labels) is MarkerSet.CGM2_4


def test_logs_chosen_set_at_info(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(
        logging.INFO,
        logger="src.shared.python.upstream_drift_tools.lab.bio.marker_sets",
    )
    labels = list(CANONICAL_LABELS[MarkerSet.GOLF_CLUSTER])
    detect_marker_set(labels)
    assert any("matched GOLF_CLUSTER" in rec.message for rec in caplog.records)


def test_missing_required_for_known_set() -> None:
    labels = ["Marker_2:2:1", "Marker_2:2:2"]  # GOLF_CLUSTER incomplete
    missing = missing_required(MarkerSet.GOLF_CLUSTER, labels)
    assert "Marker_2:2:3" in missing
    assert "Marker_3:3:1" in missing


def test_missing_required_for_unknown_returns_empty() -> None:
    assert missing_required(MarkerSet.UNKNOWN, ["foo"]) == []
