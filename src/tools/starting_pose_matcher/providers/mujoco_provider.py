"""MuJoCo SkeletonProvider — read body world positions from an MJCF model.

Closes #4390 (MuJoCo skeleton provider parity).

Strategy:
1. Load an MJCF file via ``mujoco.MjModel.from_xml_path``.
2. Set joint positions via ``data.qpos`` (default: keyframe 0 if any,
   else zeros).
3. ``mj_forward(model, data)`` to propagate.
4. Read ``data.xpos[body_id]`` for each body in our skeleton mapping.

The mapping below uses the MuJoCo humanoid-body conventions used in
``src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/``
(pelvis, lwaist, upper_waist, torso, head, l_shoulder, r_shoulder,
upper_arm_L/R, lower_arm_L/R, hand_L/R) and maps them into the
matcher's compact short names (hip, spine, torso, hub, ls, rs, le,
re, lw, rw, mp, ch).

When the MuJoCo wheel isn't installed in the current Python env,
``is_available()`` returns False and ``get_provider("MuJoCo")`` will
raise ``ProviderUnavailable``.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import numpy as np

from src.tools.starting_pose_matcher.core import (
    FALLBACK_SEGMENTS,
    Skeleton,
    fallback_skeleton,
)
from ._base import SkeletonProvider


# MuJoCo body name → matcher short name.  Default mapping for the
# humanoid bodies typically present in MJCF files.  Override per-model
# by passing a ``body_map`` to the constructor.
_DEFAULT_BODY_MAP: dict[str, str] = {
    "pelvis":     "hip",
    "lower_waist": "spine",
    "torso":      "torso",
    "upper_torso": "hub",
    "shoulder_L": "ls",
    "shoulder_R": "rs",
    "upper_arm_L": "le",   # MuJoCo hierarchy attaches elbow at upper-arm
    "upper_arm_R": "re",
    "lower_arm_L": "lw",
    "lower_arm_R": "rw",
    "hand_L":     "mp",
    "club_head":  "ch",
}


class MujocoSkeletonProvider(SkeletonProvider):
    """Loads an MJCF + qpos and reads body world positions.

    Args:
        model_path: path to an .xml MJCF file.  If None, falls back to
            FK-derived default skeleton on every call.
        body_map: override the engine-body-name → matcher-short-name
            mapping.  Default: :data:`_DEFAULT_BODY_MAP`.
        poses: list of pose names this provider should expose.  Each
            pose should correspond to a keyframe in the MJCF whose
            name matches.  Falls back to FK-derived skeleton when the
            keyframe is missing.
    """

    engine_name: ClassVar[str] = "MuJoCo"

    def __init__(self,
                 model_path: str | Path | None = None,
                 body_map: dict[str, str] | None = None,
                 poses: tuple[str, ...] = ("Address", "TopofBackswing",
                                            "Impact")) -> None:
        self._model_path = Path(model_path) if model_path else None
        self._body_map = body_map or dict(_DEFAULT_BODY_MAP)
        self._poses = tuple(poses)
        # Cached MjModel — lazy.
        self._mj_model = None
        self._mj_data = None

    @classmethod
    def is_available(cls) -> bool:
        try:
            import mujoco  # noqa: F401
        except (ImportError, OSError):
            return False
        return True

    def list_poses(self) -> list[str]:
        return list(self._poses)

    def get_skeleton(self, pose_name: str) -> Skeleton:
        # If MuJoCo isn't actually loadable or the model file is missing,
        # gracefully fall back to the FK-derived default.
        if not self.is_available() or self._model_path is None \
                or not self._model_path.exists():
            return fallback_skeleton(pose_name)
        try:
            return self._compute(pose_name)
        except Exception:  # noqa: BLE001
            return fallback_skeleton(pose_name)

    # ------------------------------------------------------------------
    def _compute(self, pose_name: str) -> Skeleton:
        import mujoco
        if self._mj_model is None:
            self._mj_model = mujoco.MjModel.from_xml_path(str(self._model_path))
            self._mj_data = mujoco.MjData(self._mj_model)
        m = self._mj_model
        d = self._mj_data
        # Try to load a named keyframe matching pose_name; otherwise zero qpos.
        try:
            key_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, pose_name)
        except Exception:  # noqa: BLE001
            key_id = -1
        if key_id >= 0:
            mujoco.mj_resetDataKeyframe(m, d, key_id)
        else:
            mujoco.mj_resetData(m, d)
        mujoco.mj_forward(m, d)
        joints: dict[str, np.ndarray] = {}
        for body_name, short in self._body_map.items():
            try:
                bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body_name)
            except Exception:  # noqa: BLE001
                continue
            if bid < 0:
                continue
            joints[short] = np.array(d.xpos[bid], dtype=float)
        # Synthesise mp from lw + rw if the model doesn't expose a hand body.
        if "mp" not in joints and "lw" in joints and "rw" in joints:
            joints["mp"] = (joints["lw"] + joints["rw"]) / 2.0
        return Skeleton(name=pose_name, joints=joints,
                        segments=list(FALLBACK_SEGMENTS))


__all__ = ["MujocoSkeletonProvider"]
