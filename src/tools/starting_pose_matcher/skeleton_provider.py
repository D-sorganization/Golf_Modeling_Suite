"""Provider contract for starting-pose matcher skeleton sources.

The GUI works against this contract while concrete providers live under
``src.tools.starting_pose_matcher.providers``.  Provider modules for optional
engines must remain cheap to import; dependency checks belong in factories or
provider constructors, and registry failures are normalized to typed errors.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from src.tools.starting_pose_matcher.core import (
    Skeleton,
    fallback_skeleton,
    load_skeleton,
)

REQUIRED_JOINTS: tuple[str, ...] = (
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


class ProviderError(Exception):
    """Base class for provider contract and registry errors."""


class ProviderContractError(ProviderError, ValueError):
    """Raised when a provider result violates the matcher contract."""


class ProviderUnavailableError(ProviderError, RuntimeError):
    """Raised when a registered provider cannot be created in this runtime."""

    def __init__(
        self,
        provider_id: str,
        message: str,
        *,
        install_hint: str | None = None,
    ) -> None:
        self.provider_id = provider_id
        self.install_hint = install_hint
        detail = f"{provider_id}: {message}"
        if install_hint:
            detail = f"{detail} ({install_hint})"
        super().__init__(detail)


class UnknownProviderError(ProviderError, KeyError):
    """Raised when a provider ID is not registered."""


@dataclass(frozen=True)
class ProviderMetadata:
    """Serializable metadata that identifies a skeleton provider instance."""

    name: str
    engine: str
    model_path: str | None = None
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = list(self.capabilities)
        return data

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ProviderMetadata:
        return cls(
            name=str(data["name"]),
            engine=str(data["engine"]),
            model_path=(
                None if data.get("model_path") is None else str(data["model_path"])
            ),
            capabilities=tuple(str(v) for v in data.get("capabilities", ())),
        )


@runtime_checkable
class SkeletonProvider(Protocol):
    """Abstract interface for sources of model skeleton poses."""

    metadata: ProviderMetadata

    def list_poses(self) -> list[str]:
        """Return the names of the poses this provider can produce."""

    def get_skeleton(self, pose_name: str) -> Skeleton:
        """Return the :class:`Skeleton` for the named pose."""

    def get_default_pose(self) -> str:
        """Return the pose to show when a provider is first selected."""


@runtime_checkable
class ObservationProvider(Protocol):
    """Optional contract for observed-input providers such as OpenPose."""

    metadata: ProviderMetadata

    def load_observed_target(self, *args: Any, **kwargs: Any) -> Any:
        """Load observed target data from provider-specific inputs."""


def _joint_names(skeleton: Skeleton | dict[str, Any]) -> set[str]:
    if isinstance(skeleton, Skeleton):
        return set(skeleton.joints)
    return set(skeleton)


def missing_required_joints(skeleton: Skeleton | dict[str, Any]) -> tuple[str, ...]:
    """Return required matcher vocabulary entries absent from ``skeleton``."""

    names = _joint_names(skeleton)
    return tuple(name for name in REQUIRED_JOINTS if name not in names)


def validate_required_joints(
    skeleton: Skeleton | dict[str, Any],
    *,
    provider_name: str = "provider",
) -> None:
    """Raise a typed error if ``skeleton`` omits shared matcher vocabulary."""

    missing = missing_required_joints(skeleton)
    if missing:
        raise ProviderContractError(
            f"{provider_name} skeleton is missing required joints: {', '.join(missing)}"
        )


class JsonSkeletonProvider:
    """Reads ``simscape_skeleton_<pose>.json`` files from a directory.

    These files are produced by ``export_default_skeleton.m`` (MATLAB-side
    helper next to the legacy Motion Capture Plotter tree).  When a file
    is missing, falls back to :func:`core.fallback_skeleton` (which
    derives the skeleton from the shared
    :func:`reference_golfer_setup` + :func:`forward_kinematics`).
    """

    def __init__(
        self,
        json_dir: str | Path,
        poses: tuple[str, ...] = ("TopofBackswing", "Impact"),
    ) -> None:
        self._dir = Path(json_dir)
        self._poses = tuple(poses)
        self.metadata = ProviderMetadata(
            name="Simscape JSON",
            engine="simscape-json",
            model_path=str(self._dir),
            capabilities=("physics", "file", "fallback"),
        )

    def list_poses(self) -> list[str]:
        return list(self._poses)

    def get_default_pose(self) -> str:
        return self._poses[0]

    def get_skeleton(self, pose_name: str) -> Skeleton:
        path = self._dir / f"simscape_skeleton_{pose_name}.json"
        skeleton = load_skeleton(path, fallback_pose=pose_name)
        validate_required_joints(skeleton, provider_name=self.metadata.name)
        return skeleton


__all__ = [
    "JsonSkeletonProvider",
    "ObservationProvider",
    "ProviderContractError",
    "ProviderError",
    "ProviderMetadata",
    "ProviderUnavailableError",
    "REQUIRED_JOINTS",
    "SkeletonProvider",
    "UnknownProviderError",
    "fallback_skeleton",
    "missing_required_joints",
    "validate_required_joints",
]
