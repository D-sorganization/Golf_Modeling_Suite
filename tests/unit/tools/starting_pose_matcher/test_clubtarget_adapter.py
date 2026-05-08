"""Tests for the starting-pose matcher's canonical ClubTarget adapter."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from src.shared.python.motion_matching.club_target import ClubTarget, SourceProvenance
from src.tools.starting_pose_matcher import core


def _target(shaft_length_m: float = 2.0) -> ClubTarget:
    time = np.array([0.0, 0.001, 0.002], dtype=np.float64)
    butt = np.array(
        [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [0.2, 0.0, 0.0]],
        dtype=np.float64,
    )
    clubhead = butt + np.array([shaft_length_m, 0.0, 0.0])
    quat = np.tile(np.array([1.0, 0.0, 0.0, 0.0]), (time.shape[0], 1))
    return ClubTarget(
        time=time,
        butt=butt,
        clubhead=clubhead,
        club_quat=quat,
        impact_idx=2,
        source=SourceProvenance(
            filename="target.c3d",
            format="c3d",
            subject_id="T",
            trial_id="1",
            sha256="abc",
        ),
    )


def test_clubtarget_adapter_preserves_shared_loader_units() -> None:
    target = _target(shaft_length_m=2.0)

    df = core.clubtarget_to_mocap_dataframe(target)

    shaft = np.linalg.norm(
        df[["club_X", "club_Y", "club_Z"]].to_numpy()
        - df[["mid_X", "mid_Y", "mid_Z"]].to_numpy(),
        axis=1,
    )
    np.testing.assert_allclose(shaft, np.full(3, 2.0))


def test_adapter_reports_missing_required_target_fields() -> None:
    target = SimpleNamespace(
        time=np.array([0.0, 0.001]),
        butt=np.zeros((2, 3)),
        clubhead=np.ones((2, 3)),
    )

    with pytest.raises(core.ClubTargetAdapterError, match="club_quat"):
        core.clubtarget_to_mocap_dataframe(target)  # type: ignore[arg-type]


def test_load_mocap_target_dispatches_excel_with_sheet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, str | None]] = []

    def fake_load(
        path: Path, *, sheet: str | None = None, opts: object = None
    ) -> ClubTarget:
        _ = opts
        calls.append((Path(path), sheet))
        return _target()

    monkeypatch.setattr(core, "load_club_target", fake_load)

    df = core.load_mocap_target("swing.xlsx", "TW_ProV1")

    assert not df.empty
    assert calls == [(Path("swing.xlsx"), "TW_ProV1")]


def test_load_mocap_target_dispatches_c3d_without_sheet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, str | None]] = []

    def fake_load(
        path: Path, *, sheet: str | None = None, opts: object = None
    ) -> ClubTarget:
        _ = opts
        calls.append((Path(path), sheet))
        return _target()

    monkeypatch.setattr(core, "load_club_target", fake_load)

    df = core.load_mocap_target("swing.c3d", "ignored")

    assert not df.empty
    assert calls == [(Path("swing.c3d"), None)]


def test_c3d_event_header_uses_canonical_impact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(core, "load_club_target", lambda *args, **kwargs: _target())

    events = core.read_event_header("swing.c3d", "ignored")

    assert events.I_sample == 2.0
    assert events.frame_for("I") == 1
