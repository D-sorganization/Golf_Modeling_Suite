"""OpenSim SkeletonProvider — read body positions from an OSIM model.

Closes #4393 (OpenSim skeleton provider parity).

Strategy:
1. Load model via ``opensim.Model(model_path)`` and ``initSystem()``.
2. Set generalised coordinates via ``model.updCoordinateSet().get(name).setValue``.
3. Realize position: ``model.realizePosition(state)``.
4. For each named body, read
   ``body.getPositionInGround(state)`` → ``Vec3``.

When ``opensim`` isn't installed (it requires the OpenSim wheel +
matching OpenSim binaries), ``is_available()`` returns False and
``get_skeleton`` falls back to the FK-derived default.
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


_DEFAULT_BODY_MAP: dict[str, str] = {
    "pelvis":         "hip",
    "torso":          "torso",
    "ribcage":        "hub",
    "humerus_l":      "ls",
    "humerus_r":      "rs",
    "ulna_l":         "le",
    "ulna_r":         "re",
    "hand_l":         "lw",
    "hand_r":         "rw",
}


class OpenSimSkeletonProvider(SkeletonProvider):
    """OpenSim adapter.

    Args:
        model_path: ``.osim`` file path.  None falls back to FK default.
        body_map: override the body-name → matcher-short-name map.
        poses: pose names; per-pose coordinate values come from
            ``poses_coords_npz`` (a .npz keyed by pose name → dict of
            coordinate values).
        poses_coords_npz: optional .npz with the per-pose coordinate
            values.
    """

    engine_name: ClassVar[str] = "OpenSim"

    def __init__(self,
                 model_path: str | Path | None = None,
                 body_map: dict[str, str] | None = None,
                 poses: tuple[str, ...] = ("Address", "TopofBackswing",
                                            "Impact"),
                 poses_coords_npz: str | Path | None = None) -> None:
        self._model_path = Path(model_path) if model_path else None
        self._body_map = body_map or dict(_DEFAULT_BODY_MAP)
        self._poses = tuple(poses)
        self._poses_coords_npz = Path(poses_coords_npz) if poses_coords_npz else None
        self._model: Any = None
        self._state: Any = None
        self._poses_coords: dict[str, dict[str, float]] = {}

    @classmethod
    def is_available(cls) -> bool:
        try:
            import opensim  # noqa: F401
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
        import opensim as osim
        if self._model is None:
            self._model = osim.Model(str(self._model_path))
            self._state = self._model.initSystem()
            if self._poses_coords_npz is not None and self._poses_coords_npz.exists():
                # .npz of object arrays — each entry is a dict of coord_name -> value.
                npz = np.load(self._poses_coords_npz, allow_pickle=True)
                for k in npz.files:
                    raw = npz[k].item() if hasattr(npz[k], "item") else npz[k]
                    if isinstance(raw, dict):
                        self._poses_coords[k] = {str(c): float(v) for c, v in raw.items()}
        m = self._model
        s = self._state

        # Apply per-pose coordinate values.
        coords = self._poses_coords.get(pose_name, {})
        coord_set = m.getCoordinateSet()
        for i in range(coord_set.getSize()):
            c = coord_set.get(i)
            name = c.getName()
            if name in coords:
                c.setValue(s, float(coords[name]))
        m.realizePosition(s)

        joints: dict[str, np.ndarray] = {}
        body_set = m.getBodySet()
        for body_name, short in self._body_map.items():
            try:
                b = body_set.get(body_name)
            except Exception:  # noqa: BLE001
                continue
            v = b.getPositionInGround(s)
            joints[short] = np.array([v.get(0), v.get(1), v.get(2)], dtype=float)
        if "mp" not in joints and "lw" in joints and "rw" in joints:
            joints["mp"] = (joints["lw"] + joints["rw"]) / 2.0
        return Skeleton(name=pose_name, joints=joints,
                        segments=list(FALLBACK_SEGMENTS))


__all__ = ["OpenSimSkeletonProvider"]
