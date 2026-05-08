"""Simscape JSON SkeletonProvider — reads files produced by
``export_default_skeleton.m`` (a tiny MATLAB helper next to the legacy
Motion Capture Plotter directory).

This provider has no engine-library dependency; it only needs the
JSON files on disk.  Its ``is_available()`` always returns True.

Closes #4389 (promote Simscape JSON / FK support into a first-class
provider).
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from src.tools.starting_pose_matcher.core import (
    Skeleton,
    fallback_skeleton,
    load_skeleton,
)
from ._base import SkeletonProvider


class SimscapeJsonSkeletonProvider(SkeletonProvider):
    """Loads ``simscape_skeleton_<pose>.json`` files from a directory.

    These files come from running ``export_default_skeleton.m`` in
    MATLAB once per pose; they store the model's joint world positions
    at t=0 of a 5 ms simulation.

    When a file is missing, falls back to the FK-derived default
    skeleton (built from ``reference_golfer_setup`` via the shared
    motion-matching diagnostics) so the GUI always has SOMETHING to
    render — see ``core.fallback_skeleton``.
    """

    engine_name: ClassVar[str] = "Simscape"

    def __init__(self,
                 json_dir: str | Path | None = None,
                 poses: tuple[str, ...] = ("TopofBackswing", "Impact",
                                            "Address")) -> None:
        if json_dir is None:
            # Default: the legacy motion-capture-plotter directory where
            # export_default_skeleton.m writes its outputs.
            json_dir = (Path(__file__).resolve().parents[5]
                        / "src/engines/Simscape_Multibody_Models/3D_Golf_Model"
                        / "matlab/src/apps/golf_gui/Motion Capture Plotter")
        self._dir = Path(json_dir)
        self._poses = tuple(poses)

    @classmethod
    def is_available(cls) -> bool:
        # No engine library needed — JSON files only.
        return True

    def list_poses(self) -> list[str]:
        return list(self._poses)

    def get_skeleton(self, pose_name: str) -> Skeleton:
        path = self._dir / f"simscape_skeleton_{pose_name}.json"
        return load_skeleton(path, fallback_pose=pose_name)


__all__ = ["SimscapeJsonSkeletonProvider"]
