"""Pinocchio SkeletonProvider — read joint world positions via FK.

Closes #4392 (Pinocchio skeleton provider parity).

Strategy:
1. Build model + data via ``pin.buildModelFromUrdf(model_path)``.
2. Set ``q`` (default: ``pin.neutral(model)``, override via npz).
3. ``pin.forwardKinematics(model, data, q)`` then
   ``pin.updateFramePlacements(model, data)``.
4. Read each named joint via ``data.oMi[joint_id].translation``
   (joint frames) or ``data.oMf[frame_id].translation`` (named frames).

When ``pinocchio`` (``pin``) isn't installed, ``is_available`` returns
False and ``get_skeleton`` falls back to the FK-derived default.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from src.tools.starting_pose_matcher.core import (
    FALLBACK_SEGMENTS,
    Skeleton,
    fallback_skeleton,
)
from ._base import SkeletonProvider


# Pinocchio joint/frame name -> matcher short name.
_DEFAULT_JOINT_MAP: dict[str, str] = {
    "pelvis":         "hip",
    "lower_torso":    "spine",
    "torso":          "torso",
    "upper_torso":    "hub",
    "left_shoulder":  "ls",
    "right_shoulder": "rs",
    "left_elbow":     "le",
    "right_elbow":    "re",
    "left_wrist":     "lw",
    "right_wrist":    "rw",
    "club_head":      "ch",
}


class PinocchioSkeletonProvider(SkeletonProvider):
    """Pinocchio adapter.

    Args:
        model_path: URDF file path.  None falls back to FK default.
        joint_map: override the joint-name → matcher-short-name map.
        poses: pose names; q for each comes from ``poses_q_npz`` if
            provided, else ``pin.neutral(model)``.
        poses_q_npz: optional .npz keyed by pose name → q vector.
    """

    engine_name: ClassVar[str] = "Pinocchio"

    def __init__(self,
                 model_path: str | Path | None = None,
                 joint_map: dict[str, str] | None = None,
                 poses: tuple[str, ...] = ("Address", "TopofBackswing",
                                            "Impact"),
                 poses_q_npz: str | Path | None = None) -> None:
        self._model_path = Path(model_path) if model_path else None
        self._joint_map = joint_map or dict(_DEFAULT_JOINT_MAP)
        self._poses = tuple(poses)
        self._poses_q_npz = Path(poses_q_npz) if poses_q_npz else None
        self._model: Any = None
        self._data: Any = None
        self._poses_q: dict[str, np.ndarray] = {}

    @classmethod
    def is_available(cls) -> bool:
        try:
            import pinocchio  # noqa: F401
        except (ImportError, OSError):
            return False
        return True

    def list_poses(self) -> list[str]:
        return list(self._poses)

    def get_skeleton(self, pose_name: str) -> Skeleton:
        if not self.is_available() or self._model_path is None \
                or not self._model_path.exists():
            return fallback_skeleton(pose_name)
        try:
            return self._compute(pose_name)
        except Exception:  # noqa: BLE001
            return fallback_skeleton(pose_name)

    # ------------------------------------------------------------------
    def _compute(self, pose_name: str) -> Skeleton:
        import pinocchio as pin
        if self._model is None:
            self._model = pin.buildModelFromUrdf(str(self._model_path))
            self._data = self._model.createData()
            if self._poses_q_npz is not None and self._poses_q_npz.exists():
                npz = np.load(self._poses_q_npz)
                self._poses_q = {k: np.asarray(npz[k]) for k in npz.files}
        m = self._model
        d = self._data
        q = self._poses_q.get(pose_name, pin.neutral(m))
        if q.size != m.nq:
            q = pin.neutral(m)
        pin.forwardKinematics(m, d, q)
        pin.updateFramePlacements(m, d)

        joints: dict[str, np.ndarray] = {}
        for src_name, short in self._joint_map.items():
            # Try frames first (named, more precise), then joints.
            try:
                fid = m.getFrameId(src_name)
                if fid < m.nframes:
                    joints[short] = np.array(d.oMf[fid].translation, dtype=float)
                    continue
            except Exception:  # noqa: BLE001
                pass
            try:
                jid = m.getJointId(src_name)
                if 0 < jid < m.njoints:
                    joints[short] = np.array(d.oMi[jid].translation, dtype=float)
            except Exception:  # noqa: BLE001
                continue
        if "mp" not in joints and "lw" in joints and "rw" in joints:
            joints["mp"] = (joints["lw"] + joints["rw"]) / 2.0
        return Skeleton(name=pose_name, joints=joints,
                        segments=list(FALLBACK_SEGMENTS))


__all__ = ["PinocchioSkeletonProvider"]
