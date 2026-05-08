"""Simscape starting-pose skeleton providers.

The current first-class Simscape provider consumes the JSON files emitted
by the MATLAB ``export_default_skeleton.m`` helper.  Missing JSON files
still fall back to the shared FK/reference-golfer skeletons so the
starting-pose matcher remains usable before the MATLAB export is run.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from src.tools.starting_pose_matcher.core import (
    FALLBACK_SEGMENTS,
    Skeleton,
    fallback_skeleton,
)

logger = logging.getLogger(__name__)

SimscapeModelId = Literal["3D_Golf_Model", "3D_FullBody_Model"]
SimscapeExportMode = Literal["json", "live_matlab_simulink"]

SIMSCAPE_JSON_FILENAME_TEMPLATE = "simscape_skeleton_{pose}.json"
SIMSCAPE_REQUIRED_JOINTS: tuple[str, ...] = (
    "hip",
    "spine",
    "torso",
    "hub",
    "ls",
    "rs",
    "le",
    "re",
    "lw",
    "rw",
    "mp",
    "ch",
)


@dataclass(frozen=True)
class SimscapeProviderMetadata:
    """Provider metadata exposed to UI/registry layers."""

    provider_id: str
    display_name: str
    model_id: SimscapeModelId
    export_mode: SimscapeExportMode
    units: str
    coordinate_frame: str
    filename_template: str
    live_export_supported: bool = False


class SimscapeProviderError(ValueError):
    """Base error for invalid Simscape starting-pose provider inputs."""


class SimscapeJsonProviderError(SimscapeProviderError):
    """Raised when a Simscape skeleton JSON file is present but malformed."""


class SimscapeJsonProvider:
    """Read Simscape skeleton JSON files with FK fallback for missing files."""

    def __init__(
        self,
        json_dir: str | Path,
        poses: tuple[str, ...] = ("TopofBackswing", "Impact"),
        *,
        model_id: SimscapeModelId = "3D_Golf_Model",
    ) -> None:
        self._dir = Path(json_dir)
        self._poses = tuple(poses)
        self.metadata = SimscapeProviderMetadata(
            provider_id="simscape-json",
            display_name="Simscape JSON skeleton export",
            model_id=model_id,
            export_mode="json",
            units="m",
            coordinate_frame="Simscape world frame, Z-up",
            filename_template=SIMSCAPE_JSON_FILENAME_TEMPLATE,
            live_export_supported=False,
        )

    def list_poses(self) -> list[str]:
        return list(self._poses)

    def get_skeleton(self, pose_name: str) -> Skeleton:
        path = self._dir / SIMSCAPE_JSON_FILENAME_TEMPLATE.format(pose=pose_name)
        if path.exists():
            return _load_simscape_json(path, fallback_pose=pose_name)

        logger.warning(
            "%s not found - using FK-derived fallback %s pose. Run "
            "export_default_skeleton('%s') in MATLAB for actual model joints.",
            path,
            pose_name,
            pose_name,
        )
        return fallback_skeleton(pose_name)


def create_provider(
    json_dir: str | Path,
    poses: tuple[str, ...] = ("TopofBackswing", "Impact"),
    *,
    model_id: SimscapeModelId = "3D_Golf_Model",
) -> SimscapeJsonProvider:
    """Factory hook used by provider registries when present."""

    return SimscapeJsonProvider(json_dir=json_dir, poses=poses, model_id=model_id)


def _load_simscape_json(json_path: Path, *, fallback_pose: str) -> Skeleton:
    try:
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise SimscapeJsonProviderError(
            f"Malformed Simscape skeleton JSON {json_path}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise SimscapeJsonProviderError(
            f"Could not read Simscape skeleton JSON {json_path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SimscapeJsonProviderError(
            f"Malformed Simscape skeleton JSON {json_path}: root must be an object"
        )

    joints = _parse_joints(data.get("joints"), json_path)
    segments = _parse_segments(data.get("segments", []), json_path)
    pose = data.get("pose", fallback_pose)
    if not isinstance(pose, str):
        raise SimscapeJsonProviderError(
            f"Malformed Simscape skeleton JSON {json_path}: pose must be a string"
        )

    return Skeleton(
        name=pose,
        joints=joints,
        segments=segments or list(FALLBACK_SEGMENTS),
    )


def _parse_joints(raw_joints: object, json_path: Path) -> dict[str, np.ndarray]:
    if not isinstance(raw_joints, dict):
        raise SimscapeJsonProviderError(
            f"Malformed Simscape skeleton JSON {json_path}: joints must be an object"
        )

    joints: dict[str, np.ndarray] = {}
    for name, raw_value in raw_joints.items():
        if not isinstance(name, str):
            raise SimscapeJsonProviderError(
                f"Malformed Simscape skeleton JSON {json_path}: joint names must be strings"
            )
        try:
            point = np.asarray(raw_value, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise SimscapeJsonProviderError(
                f"Malformed Simscape skeleton JSON {json_path}: joint {name!r} "
                "must contain numeric coordinates"
            ) from exc
        if point.shape != (3,):
            raise SimscapeJsonProviderError(
                f"Malformed Simscape skeleton JSON {json_path}: joint {name!r} "
                "must contain exactly three coordinates"
            )
        if not np.all(np.isfinite(point)):
            raise SimscapeJsonProviderError(
                f"Malformed Simscape skeleton JSON {json_path}: joint {name!r} "
                "contains non-finite coordinates"
            )
        joints[name] = point

    missing = sorted(set(SIMSCAPE_REQUIRED_JOINTS) - joints.keys())
    if missing:
        missing_text = ", ".join(missing)
        raise SimscapeJsonProviderError(
            f"Malformed Simscape skeleton JSON {json_path}: missing required "
            f"joints: {missing_text}"
        )

    return joints


def _parse_segments(raw_segments: object, json_path: Path) -> list[tuple[str, str]]:
    if raw_segments in (None, []):
        return []
    if not isinstance(raw_segments, list):
        raise SimscapeJsonProviderError(
            f"Malformed Simscape skeleton JSON {json_path}: segments must be a list"
        )

    segments: list[tuple[str, str]] = []
    for segment in raw_segments:
        if (
            not isinstance(segment, list)
            or len(segment) != 2
            or not all(isinstance(item, str) for item in segment)
        ):
            raise SimscapeJsonProviderError(
                f"Malformed Simscape skeleton JSON {json_path}: segments must be "
                "two-item string lists"
            )
        segments.append((segment[0], segment[1]))
    return segments


# Legacy compatibility for callers that imported the old JSON provider name
# from the Simscape module after the provider split.
JsonSkeletonProvider = SimscapeJsonProvider

__all__ = [
    "SIMSCAPE_JSON_FILENAME_TEMPLATE",
    "SIMSCAPE_REQUIRED_JOINTS",
    "JsonSkeletonProvider",
    "SimscapeExportMode",
    "SimscapeJsonProvider",
    "SimscapeJsonProviderError",
    "SimscapeModelId",
    "SimscapeProviderError",
    "SimscapeProviderMetadata",
    "create_provider",
]
