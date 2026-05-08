"""Simscape starting-pose skeleton providers.

The current first-class Simscape provider consumes the JSON files emitted
by the MATLAB ``export_default_skeleton.m`` helper.  Missing JSON files
still fall back to the shared FK/reference-golfer skeletons so the
starting-pose matcher remains usable before the MATLAB export is run.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

import numpy as np
from scipy.io import loadmat, savemat

from src.tools.starting_pose_matcher.core import (
    FALLBACK_SEGMENTS,
    RigidTransform,
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
SIMSCAPE_REQUIRED_MAT_FIELDS_3D_GOLF: tuple[str, ...] = (
    "TranslationStartPositionX",
    "TranslationStartPositionY",
    "TranslationStartPositionZ",
    "HipStartPositionZ",
    "LSStartPositionY",
    "RSStartPositionY",
    "LEStartPosition",
    "REStartPosition",
)
SIMSCAPE_FULL_BODY_OPTIONAL_FIELD_PREFIXES: tuple[str, ...] = (
    "LHip",
    "RHip",
    "LKnee",
    "RKnee",
    "LAnkle",
    "RAnkle",
)
_MAT_META_KEYS = {"__header__", "__version__", "__globals__"}
_START_FIELD_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9]*(StartPosition|StartVelocity)[XYZ]?$"
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


class SimscapeMatEditorError(SimscapeProviderError):
    """Raised for invalid Simscape input-MAT editor operations."""


@dataclass(frozen=True)
class SimscapeMatField:
    """Editable scalar Simscape start-state field in UI units."""

    name: str
    value: float
    unit: str
    kind: Literal["position", "velocity"]
    model_scope: Literal["legacy_3d_golf", "full_body_optional", "generic"]


@dataclass(frozen=True)
class SimscapeMatEditSession:
    """MAT editor state that is safe to persist in matcher sessions."""

    source_path: str | None = None
    written_path: str | None = None


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


def load_simscape_input_mat(path: str | Path) -> dict[str, object]:
    """Load a Simscape input MAT file using SciPy."""

    path = Path(path)
    try:
        return dict(loadmat(path, squeeze_me=True, struct_as_record=False))
    except Exception as exc:  # noqa: BLE001 - scipy raises several MAT errors
        raise SimscapeMatEditorError(
            f"Could not load Simscape MAT file {path}: {exc}"
        ) from exc


def discover_simscape_start_fields(
    mat_data: Mapping[str, object],
    *,
    model_id: SimscapeModelId = "3D_Golf_Model",
) -> list[SimscapeMatField]:
    """Discover editable scalar start-position/start-velocity fields.

    Values are returned in the same units the UI edits: root translation in
    metres, angular joints in degrees, root translation velocities in m/s, and
    angular velocities in deg/s.
    """

    fields: list[SimscapeMatField] = []
    for name in sorted(mat_data):
        if name in _MAT_META_KEYS or not _START_FIELD_RE.match(name):
            continue
        value = _scalar_float(name, mat_data[name])
        if value is None:
            continue
        fields.append(
            SimscapeMatField(
                name=name,
                value=value,
                unit=_field_unit(name),
                kind="velocity" if "StartVelocity" in name else "position",
                model_scope=_field_model_scope(name, model_id=model_id),
            )
        )
    return fields


def validate_simscape_start_fields(
    mat_data: Mapping[str, object],
    *,
    model_id: SimscapeModelId = "3D_Golf_Model",
) -> list[SimscapeMatField]:
    """Return editable fields or raise an explicit missing/invalid error."""

    fields = discover_simscape_start_fields(mat_data, model_id=model_id)
    by_name = {field.name: field for field in fields}
    required = SIMSCAPE_REQUIRED_MAT_FIELDS_3D_GOLF
    missing = [name for name in required if name not in by_name]
    if missing:
        raise SimscapeMatEditorError(
            "Simscape MAT file missing required current-model start fields: "
            + ", ".join(missing)
        )
    if model_id == "3D_FullBody_Model":
        full_body_present = any(
            name.startswith(SIMSCAPE_FULL_BODY_OPTIONAL_FIELD_PREFIXES)
            for name in by_name
        )
        if not full_body_present:
            raise SimscapeMatEditorError(
                "Full-body Simscape MAT files must include at least one full-body "
                "start field such as LHipStartPositionX, LKneeStartPosition, or "
                "LAnkleStartPositionX"
            )
    return fields


def apply_matcher_transform_overlay(
    fields: Mapping[str, float],
    transform: RigidTransform,
) -> dict[str, float]:
    """Overlay the matcher transform onto editable values without mutation."""

    edited = dict(fields)
    translation_overlay = {
        "TranslationStartPositionX": transform.tx,
        "TranslationStartPositionY": transform.ty,
        "TranslationStartPositionZ": transform.tz,
    }
    for name, delta in translation_overlay.items():
        if name in edited:
            edited[name] = float(edited[name]) + float(delta)

    rotation_overlay = {
        "HipStartPositionX": transform.rx,
        "HipStartPositionY": transform.ry,
        "HipStartPositionZ": transform.rz,
    }
    for name, delta in rotation_overlay.items():
        if name in edited:
            edited[name] = float(edited[name]) + float(delta)
    return edited


def default_simscape_output_mat_path(
    source_path: str | Path,
    *,
    timestamp: datetime | str | None = None,
) -> Path:
    """Return ``<stem>_starting_pose_<timestamp>.mat`` beside the source."""

    source = Path(source_path)
    if timestamp is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    elif isinstance(timestamp, datetime):
        ts = timestamp.strftime("%Y%m%d_%H%M%S")
    else:
        ts = timestamp
    return source.with_name(f"{source.stem}_starting_pose_{ts}{source.suffix}")


def save_simscape_input_mat(
    mat_data: Mapping[str, object],
    edits: Mapping[str, float],
    output_path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write a Simscape input MAT copy with scalar edits applied."""

    output = Path(output_path)
    if output.exists() and not overwrite:
        raise SimscapeMatEditorError(
            f"Refusing to overwrite existing MAT file: {output}"
        )

    writable: dict[str, object] = {}
    for name, value in mat_data.items():
        if name in _MAT_META_KEYS:
            continue
        writable[name] = (
            np.array(value, copy=True) if isinstance(value, np.ndarray) else value
        )

    unknown = sorted(set(edits) - set(writable))
    if unknown:
        raise SimscapeMatEditorError(
            "Cannot edit fields that are not present in the source MAT: "
            + ", ".join(unknown)
        )
    for name, value in edits.items():
        _require_scalar_field(name, writable[name])
        writable[name] = np.array(float(value))

    output.parent.mkdir(parents=True, exist_ok=True)
    savemat(output, writable)
    return output


def _scalar_float(name: str, value: object) -> float | None:
    try:
        array = np.asarray(value)
    except (TypeError, ValueError):
        return None
    if array.size != 1:
        raise SimscapeMatEditorError(
            f"Editable Simscape MAT field {name} is not scalar"
        )
    try:
        scalar = float(array.reshape(-1)[0])
    except (TypeError, ValueError) as exc:
        raise SimscapeMatEditorError(
            f"Editable Simscape MAT field {name} is not numeric"
        ) from exc
    if not np.isfinite(scalar):
        raise SimscapeMatEditorError(
            f"Editable Simscape MAT field {name} must be finite"
        )
    return scalar


def _require_scalar_field(name: str, value: object) -> None:
    if _scalar_float(name, value) is None:
        raise SimscapeMatEditorError(f"Editable Simscape MAT field {name} is invalid")


def _field_unit(name: str) -> str:
    is_translation = name.startswith("TranslationStart")
    is_velocity = "StartVelocity" in name
    if is_translation and is_velocity:
        return "m/s"
    if is_translation:
        return "m"
    if is_velocity:
        return "deg/s"
    return "deg"


def _field_model_scope(
    name: str, *, model_id: SimscapeModelId
) -> Literal["legacy_3d_golf", "full_body_optional", "generic"]:
    if name in SIMSCAPE_REQUIRED_MAT_FIELDS_3D_GOLF:
        return "legacy_3d_golf"
    if name.startswith(SIMSCAPE_FULL_BODY_OPTIONAL_FIELD_PREFIXES):
        return "full_body_optional"
    return "generic"


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
    "SIMSCAPE_FULL_BODY_OPTIONAL_FIELD_PREFIXES",
    "SIMSCAPE_REQUIRED_MAT_FIELDS_3D_GOLF",
    "SIMSCAPE_REQUIRED_JOINTS",
    "JsonSkeletonProvider",
    "SimscapeExportMode",
    "SimscapeJsonProvider",
    "SimscapeJsonProviderError",
    "SimscapeMatEditSession",
    "SimscapeMatEditorError",
    "SimscapeMatField",
    "SimscapeModelId",
    "SimscapeProviderError",
    "SimscapeProviderMetadata",
    "apply_matcher_transform_overlay",
    "create_provider",
    "default_simscape_output_mat_path",
    "discover_simscape_start_fields",
    "load_simscape_input_mat",
    "save_simscape_input_mat",
    "validate_simscape_start_fields",
]
