"""Provider contract for starting-pose skeleton sources.

The GUI should eventually talk only to this provider surface: providers
enumerate model poses and return joint positions in the shared matcher
vocabulary.  The Simscape JSON implementation now lives under
``providers/``; ``JsonSkeletonProvider`` remains as a compatibility alias
for existing imports while the GUI migration proceeds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.tools.starting_pose_matcher.core import Skeleton, fallback_skeleton

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


@dataclass(frozen=True)
class ProviderMetadata:
    """Serializable provider identity and capability metadata."""

    name: str
    engine: str
    model_path: str | None = None
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    def to_session_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for session files."""
        data = asdict(self)
        data["capabilities"] = list(self.capabilities)
        return data


class ProviderError(RuntimeError):
    """Base class for user-actionable provider failures."""


class ProviderUnavailableError(ProviderError):
    """Raised when an optional provider cannot run in this environment."""

    def __init__(
        self,
        provider_id: str,
        reason: str,
        *,
        install_hint: str | None = None,
    ) -> None:
        message = f"Provider '{provider_id}' is unavailable: {reason}"
        if install_hint:
            message = f"{message}. {install_hint}"
        super().__init__(message)
        self.provider_id = provider_id
        self.reason = reason
        self.install_hint = install_hint


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid or incomplete."""


class ProviderValidationError(ProviderError):
    """Raised when a provider returns an invalid skeleton contract."""


def validate_required_joints(
    skeleton: Skeleton,
    *,
    provider_id: str,
    required: tuple[str, ...] = REQUIRED_JOINTS,
) -> None:
    """Validate that a provider skeleton includes the shared vocabulary."""
    missing = [joint for joint in required if joint not in skeleton.joints]
    if missing:
        missing_text = ", ".join(missing)
        raise ProviderValidationError(
            f"Provider '{provider_id}' returned pose '{skeleton.name}' "
            f"without required joints: {missing_text}"
        )


class SkeletonProvider(ABC):
    """Abstract interface for sources of model skeleton poses."""

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return serializable provider metadata."""

    @abstractmethod
    def list_poses(self) -> list[str]:
        """Return the names of the poses this provider can produce."""

    @abstractmethod
    def get_skeleton(self, pose_name: str) -> Skeleton:
        """Return the :class:`Skeleton` for the named pose."""

    def get_default_pose(self) -> str | None:
        """Return the preferred initial pose, if the provider exposes one."""
        poses = self.list_poses()
        return poses[0] if poses else None

    def load_observed_target(self, _source: str | Path, **_kwargs: Any) -> Any:
        """Load an observed target for observation providers.

        Physics-engine skeleton providers do not implement this optional
        hook.  Observation providers should override it.
        """
        raise ProviderConfigurationError(
            f"Provider '{self.metadata.name}' does not load observed targets"
        )


from src.tools.starting_pose_matcher.providers.simscape_json import (  # noqa: E402
    SimscapeJsonSkeletonProvider,
)

JsonSkeletonProvider = SimscapeJsonSkeletonProvider

__all__ = [
    "JsonSkeletonProvider",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderMetadata",
    "ProviderUnavailableError",
    "ProviderValidationError",
    "REQUIRED_JOINTS",
    "SimscapeJsonSkeletonProvider",
    "SkeletonProvider",
    "fallback_skeleton",
    "validate_required_joints",
]
