from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import pytest
from src.engines.physics_engines.opensim.python.opensim_golf.fk import (
    compute_clubhead,
    compute_grip,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = (
    REPO_ROOT
    / "src"
    / "engines"
    / "physics_engines"
    / "opensim"
    / "models"
    / "golf_humanoid.osim"
)

_OPENSIM_AVAILABLE = importlib.util.find_spec("opensim") is not None
_GRIP_FRAME_PATH = "/jointset/hand_r_to_club/hand_r_grip_offset"
_CLUBHEAD_FRAME_PATH = "/jointset/hand_r_to_club/club_head_offset"


class _FakeVec3:
    def __init__(self, values: tuple[float, float, float]) -> None:
        self._values = values

    def get(self, index: int) -> float:
        return self._values[index]


class _FakeRotation:
    def get(self, row: int, col: int) -> float:
        return 1.0 if row == col else 0.0


class _FakeTransform:
    def __init__(self, values: tuple[float, float, float]) -> None:
        self._vec = _FakeVec3(values)
        self._rot = _FakeRotation()

    def p(self) -> _FakeVec3:
        return self._vec

    def R(self) -> _FakeRotation:
        return self._rot


class _FakeFrame:
    def __init__(self, values: tuple[float, float, float]) -> None:
        self._transform = _FakeTransform(values)

    def getTransformInGround(self, state: object) -> _FakeTransform:
        return self._transform


class _FakeState:
    def isValid(self) -> bool:
        return True


class _FakeModel:
    def __init__(self) -> None:
        self.requested_paths: list[str] = []
        self.frames = {
            _GRIP_FRAME_PATH: _FakeFrame((1.0, 2.0, 3.0)),
            _CLUBHEAD_FRAME_PATH: _FakeFrame((1.0, 2.0, 4.1)),
        }

    def realizePosition(self, state: object) -> None:
        return None

    def getComponent(self, path: str) -> _FakeFrame:
        self.requested_paths.append(path)
        try:
            return self.frames[path]
        except KeyError as exc:
            raise RuntimeError(path) from exc


def test_fk_uses_canonical_opensim_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "opensim", types.SimpleNamespace())

    model = _FakeModel()
    state = _FakeState()

    grip_pos, grip_quat = compute_grip(model, state)
    clubhead_pos, clubhead_quat = compute_clubhead(model, state)

    assert model.requested_paths == [_GRIP_FRAME_PATH, _CLUBHEAD_FRAME_PATH]
    np.testing.assert_allclose(grip_pos, np.array([1.0, 2.0, 3.0]))
    np.testing.assert_allclose(clubhead_pos, np.array([1.0, 2.0, 4.1]))
    np.testing.assert_allclose(grip_quat, np.array([1.0, 0.0, 0.0, 0.0]))
    np.testing.assert_allclose(clubhead_quat, np.array([1.0, 0.0, 0.0, 0.0]))


@pytest.mark.requires_opensim
@pytest.mark.skipif(
    not _OPENSIM_AVAILABLE,
    reason="OpenSim Python bindings not installed.",
)
def test_fk_returns_finite_pose_for_committed_model() -> None:
    import opensim as osim

    model = osim.Model(str(MODEL_PATH))
    state = model.initSystem()

    grip_pos, grip_quat = compute_grip(model, state)
    clubhead_pos, clubhead_quat = compute_clubhead(model, state)

    assert np.isfinite(grip_pos).all()
    assert np.isfinite(grip_quat).all()
    assert np.isfinite(clubhead_pos).all()
    assert np.isfinite(clubhead_quat).all()
    assert 0.25 < np.linalg.norm(clubhead_pos - grip_pos) < 2.0
    assert np.isclose(np.linalg.norm(grip_quat), 1.0, atol=1e-6)
    assert np.isclose(np.linalg.norm(clubhead_quat), 1.0, atol=1e-6)
