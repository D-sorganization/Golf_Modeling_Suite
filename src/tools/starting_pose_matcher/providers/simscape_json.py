"""Default Simscape JSON skeleton provider."""

from __future__ import annotations

from pathlib import Path

from src.tools.starting_pose_matcher.core import Skeleton, load_skeleton
from src.tools.starting_pose_matcher.skeleton_provider import (
    ProviderMetadata,
    SkeletonProvider,
    validate_required_joints,
)

DEFAULT_POSES: tuple[str, ...] = ("TopofBackswing", "Impact")


class SimscapeJsonSkeletonProvider(SkeletonProvider):
    """Reads ``simscape_skeleton_<pose>.json`` files from a directory.

    These files are produced by ``export_default_skeleton.m``.  Missing
    files still use the FK-derived fallback path through ``core.load_skeleton``.
    """

    def __init__(
        self,
        json_dir: str | Path,
        poses: tuple[str, ...] = DEFAULT_POSES,
    ) -> None:
        self._dir = Path(json_dir)
        self._poses = tuple(poses)

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="simscape-json",
            engine="simscape",
            model_path=str(self._dir),
            capabilities=("skeleton", "json", "fallback"),
        )

    def list_poses(self) -> list[str]:
        return list(self._poses)

    def get_default_pose(self) -> str | None:
        return (
            "TopofBackswing"
            if "TopofBackswing" in self._poses
            else super().get_default_pose()
        )

    def get_skeleton(self, pose_name: str) -> Skeleton:
        path = self._dir / f"simscape_skeleton_{pose_name}.json"
        skeleton = load_skeleton(path, fallback_pose=pose_name)
        validate_required_joints(skeleton, provider_id=self.metadata.name)
        return skeleton
