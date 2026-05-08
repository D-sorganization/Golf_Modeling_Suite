"""Versioned session schema for starting-pose matcher state.

This module is intentionally pure Python so provider adapters and the GUI can
share a durable JSON contract without importing Qt or optional physics stacks.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

SESSION_SCHEMA_VERSION = 4
SKELETON_VOCABULARY_VERSION = "starting-pose-v1"

SUPPORTED_PROVIDER_IDS: frozenset[str] = frozenset(
    {
        "simscape",
        "mujoco",
        "drake",
        "pinocchio",
        "opensim",
        "openpose",
        "mediapipe",
    }
)

REQUIRED_SKELETON_JOINTS: tuple[str, ...] = (
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

OBSERVED_PROVIDER_IDS: frozenset[str] = frozenset({"openpose", "mediapipe"})
OBSERVED_REQUIRED_JOINTS: tuple[str, ...] = (
    "hip",
    "spine",
    "ls",
    "rs",
    "le",
    "re",
    "lw",
    "rw",
)


class SessionSchemaError(ValueError):
    """Raised when a session payload cannot be used safely."""


@dataclass(frozen=True)
class TargetSourceMetadata:
    """Source motion target metadata stored with a session."""

    source_type: str
    path: str
    sheet: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderMetadata:
    """Provider selection and provider-specific metadata."""

    provider_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_provider_id(self.provider_id)


@dataclass(frozen=True)
class SelectedFrame:
    """Selected event/phase frame in the target source."""

    event: str
    frame_index: int
    phase: str | None = None


@dataclass(frozen=True)
class SessionTransform:
    """Matcher 7-DOF transform stored in stable Tx/Ty/Tz/Rx/Ry/Rz form."""

    tx: float = 0.0
    ty: float = 0.0
    tz: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0
    scale: float = 1.0


@dataclass(frozen=True)
class StartingPoseSession:
    """Durable starting-pose matcher session payload."""

    version: int
    target_source: TargetSourceMetadata
    provider: ProviderMetadata
    model_path: str
    config_path: str | None
    selected_frame: SelectedFrame
    skeleton_vocabulary_version: str
    transform: SessionTransform
    quality_metrics: dict[str, float] = field(default_factory=dict)
    simscape_mat_output_path: str | None = None

    def __post_init__(self) -> None:
        validate_session_version(self.version)
        validate_provider_id(self.provider.provider_id)
        if self.skeleton_vocabulary_version != SKELETON_VOCABULARY_VERSION:
            raise SessionSchemaError(
                "Unsupported skeleton vocabulary version "
                f"{self.skeleton_vocabulary_version!r}; expected "
                f"{SKELETON_VOCABULARY_VERSION!r}."
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert this session to a JSON-serializable dictionary."""

        return asdict(self)


def validate_session_version(version: int) -> None:
    """Require the current durable schema version with a clear error."""

    if version == SESSION_SCHEMA_VERSION:
        return
    if version < SESSION_SCHEMA_VERSION:
        raise SessionSchemaError(
            "Unsupported starting-pose session schema version "
            f"{version}; expected {SESSION_SCHEMA_VERSION}. Re-save the "
            "session with a current UpstreamDrift build or run a migration."
        )
    raise SessionSchemaError(
        "Starting-pose session schema version "
        f"{version} is newer than supported {SESSION_SCHEMA_VERSION}; update "
        "UpstreamDrift before loading this file."
    )


def validate_provider_id(provider_id: str) -> None:
    """Validate provider identifiers with an actionable message."""

    if provider_id in SUPPORTED_PROVIDER_IDS:
        return
    supported = ", ".join(sorted(SUPPORTED_PROVIDER_IDS))
    raise SessionSchemaError(
        f"Unsupported starting-pose provider_id {provider_id!r}. "
        f"Use one of: {supported}."
    )


def session_from_dict(payload: Mapping[str, Any]) -> StartingPoseSession:
    """Parse and validate a durable session payload."""

    version = int(payload.get("version", payload.get("schema_version", 0)))
    validate_session_version(version)

    target = payload.get("target_source")
    provider = payload.get("provider")
    selected = payload.get("selected_frame")
    transform = payload.get("transform")
    if not isinstance(target, Mapping):
        raise SessionSchemaError("Session is missing target_source metadata.")
    if not isinstance(provider, Mapping):
        raise SessionSchemaError("Session is missing provider metadata.")
    if not isinstance(selected, Mapping):
        raise SessionSchemaError("Session is missing selected_frame metadata.")
    if not isinstance(transform, Mapping):
        raise SessionSchemaError("Session is missing transform metadata.")

    return StartingPoseSession(
        version=version,
        target_source=TargetSourceMetadata(
            source_type=str(target.get("source_type", "")),
            path=str(target.get("path", "")),
            sheet=_optional_str(target.get("sheet")),
            metadata=dict(target.get("metadata", {})),
        ),
        provider=ProviderMetadata(
            provider_id=str(provider.get("provider_id", "")),
            metadata=dict(provider.get("metadata", {})),
        ),
        model_path=str(payload.get("model_path", "")),
        config_path=_optional_str(payload.get("config_path")),
        selected_frame=SelectedFrame(
            event=str(selected.get("event", "")),
            frame_index=int(selected.get("frame_index", 0)),
            phase=_optional_str(selected.get("phase")),
        ),
        skeleton_vocabulary_version=str(payload.get("skeleton_vocabulary_version", "")),
        transform=SessionTransform(
            tx=float(transform.get("tx", 0.0)),
            ty=float(transform.get("ty", 0.0)),
            tz=float(transform.get("tz", 0.0)),
            rx=float(transform.get("rx", 0.0)),
            ry=float(transform.get("ry", 0.0)),
            rz=float(transform.get("rz", 0.0)),
            scale=float(transform.get("scale", 1.0)),
        ),
        quality_metrics={
            str(key): float(value)
            for key, value in dict(payload.get("quality_metrics", {})).items()
        },
        simscape_mat_output_path=_optional_str(payload.get("simscape_mat_output_path")),
    )


def validate_provider_parity(
    provider_id: str,
    skeleton: Mapping[str, object],
    *,
    units: str,
    coordinate_frame: str,
    optional_dependency_behavior: str,
) -> dict[str, Any]:
    """Validate the cross-provider skeleton parity contract.

    Returns a normalized matrix row used by tests and docs.
    """

    validate_provider_id(provider_id)
    required = (
        OBSERVED_REQUIRED_JOINTS
        if provider_id in OBSERVED_PROVIDER_IDS
        else REQUIRED_SKELETON_JOINTS
    )
    missing = [joint for joint in required if joint not in skeleton]
    if missing:
        raise SessionSchemaError(
            f"Provider {provider_id!r} missing required skeleton joints: "
            f"{', '.join(missing)}."
        )
    if not units:
        raise SessionSchemaError(f"Provider {provider_id!r} must declare units.")
    if not coordinate_frame:
        raise SessionSchemaError(
            f"Provider {provider_id!r} must declare a coordinate frame."
        )
    if "typed" not in optional_dependency_behavior.lower():
        raise SessionSchemaError(
            f"Provider {provider_id!r} must document typed optional-dependency "
            "behavior."
        )
    return {
        "provider_id": provider_id,
        "required_joints": list(required),
        "units": units,
        "coordinate_frame": coordinate_frame,
        "optional_dependency_behavior": optional_dependency_behavior,
    }


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
