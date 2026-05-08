"""Drake SkeletonProvider — read body world poses from a MultibodyPlant.

Closes #4391 (Drake skeleton provider parity).

Strategy:
1. Build a ``MultibodyPlant`` from URDF/SDF via
   ``Parser.AddModels(model_path)``.
2. ``plant.Finalize()``.
3. Set ``q`` via ``plant.SetPositions(plant_context, q)`` (default:
   zeros, or the named pose if provided).
4. Query each named body:
   ``plant.EvalBodyPoseInWorld(plant_context, body).translation()``.
5. Map Drake body names to the matcher's short names.

When ``pydrake`` isn't installed, ``is_available()`` returns False and
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
    "lower_torso":    "spine",
    "torso":          "torso",
    "upper_torso":    "hub",
    "left_shoulder":  "ls",
    "right_shoulder": "rs",
    "left_elbow":     "le",
    "right_elbow":    "re",
    "left_wrist":     "lw",
    "right_wrist":    "rw",
    "club":           "ch",
}


class DrakeSkeletonProvider(SkeletonProvider):
    """Drake MultibodyPlant adapter.

    Args:
        model_path: URDF/SDF file path.  If None, falls back to
            FK-derived default skeleton.
        body_map: override the body-name → matcher-short-name map.
        poses: pose names — each may map to a stored q in
            ``poses_q_npz`` (a .npz keyed by pose name) when the user
            supplies one; otherwise q=zeros for every pose.
        poses_q_npz: optional path to an ``.npz`` whose keys are pose
            names and whose values are 1-D ``q`` vectors.
    """

    engine_name: ClassVar[str] = "Drake"

    def __init__(self,
                 model_path: str | Path | None = None,
                 body_map: dict[str, str] | None = None,
                 poses: tuple[str, ...] = ("Address", "TopofBackswing",
                                            "Impact"),
                 poses_q_npz: str | Path | None = None) -> None:
        self._model_path = Path(model_path) if model_path else None
        self._body_map = body_map or dict(_DEFAULT_BODY_MAP)
        self._poses = tuple(poses)
        self._poses_q_npz = Path(poses_q_npz) if poses_q_npz else None
        self._plant: Any = None
        self._plant_context: Any = None
        self._poses_q: dict[str, np.ndarray] = {}

    @classmethod
    def is_available(cls) -> bool:
        try:
            import pydrake.multibody.plant  # noqa: F401
            import pydrake.multibody.parsing  # noqa: F401
            import pydrake.systems.framework  # noqa: F401
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
        from pydrake.multibody.parsing import Parser
        from pydrake.multibody.plant import AddMultibodyPlantSceneGraph
        from pydrake.systems.framework import DiagramBuilder

        if self._plant is None:
            builder = DiagramBuilder()
            self._plant, _ = AddMultibodyPlantSceneGraph(builder, time_step=0.0)
            Parser(self._plant).AddModels(str(self._model_path))
            self._plant.Finalize()
            diagram = builder.Build()
            diagram_context = diagram.CreateDefaultContext()
            self._plant_context = self._plant.GetMyMutableContextFromRoot(
                diagram_context)
            if self._poses_q_npz is not None and self._poses_q_npz.exists():
                npz = np.load(self._poses_q_npz)
                self._poses_q = {k: np.asarray(npz[k]) for k in npz.files}

        plant = self._plant
        ctx = self._plant_context
        nq = plant.num_positions()
        q = self._poses_q.get(pose_name, np.zeros(nq))
        if q.size != nq:
            q = np.zeros(nq)
        plant.SetPositions(ctx, q)

        joints: dict[str, np.ndarray] = {}
        for body_name, short in self._body_map.items():
            try:
                body = plant.GetBodyByName(body_name)
            except Exception:  # noqa: BLE001
                continue
            X_WB = plant.EvalBodyPoseInWorld(ctx, body)
            joints[short] = np.array(X_WB.translation(), dtype=float)
        if "mp" not in joints and "lw" in joints and "rw" in joints:
            joints["mp"] = (joints["lw"] + joints["rw"]) / 2.0
        return Skeleton(name=pose_name, joints=joints,
                        segments=list(FALLBACK_SEGMENTS))


__all__ = ["DrakeSkeletonProvider"]
