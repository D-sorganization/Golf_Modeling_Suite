"""Lazy provider registry for the starting-pose matcher."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from src.tools.starting_pose_matcher.skeleton_provider import (
    JsonSkeletonProvider,
    ProviderMetadata,
    ProviderUnavailableError,
    SkeletonProvider,
    UnknownProviderError,
)

ProviderFactory = Callable[..., SkeletonProvider]


@dataclass(frozen=True)
class ProviderRegistration:
    """Registry entry that can construct a provider without eager imports."""

    provider_id: str
    metadata: ProviderMetadata
    factory: ProviderFactory


def _load_factory(
    provider_id: str,
    module_name: str,
    *,
    install_hint: str,
    function_name: str = "create_provider",
) -> ProviderFactory:
    def factory(**kwargs: Any) -> SkeletonProvider:
        try:
            module = import_module(module_name)
        except ImportError as exc:
            raise ProviderUnavailableError(
                provider_id,
                f"failed to import provider module {module_name!r}",
                install_hint=install_hint,
            ) from exc

        create_provider = getattr(module, function_name)
        try:
            return create_provider(**kwargs)
        except ImportError as exc:
            raise ProviderUnavailableError(
                provider_id,
                "optional dependency is not installed",
                install_hint=install_hint,
            ) from exc
        except Exception as exc:
            if exc.__class__.__name__.endswith("NotAvailableError"):
                raise ProviderUnavailableError(
                    provider_id,
                    str(exc),
                    install_hint=install_hint,
                ) from exc
            raise

    return factory


def _json_factory(**kwargs: Any) -> JsonSkeletonProvider:
    json_dir = kwargs.pop("json_dir", kwargs.pop("model_path", None))
    if json_dir is None:
        json_dir = Path.cwd()
    return JsonSkeletonProvider(json_dir=json_dir, **kwargs)


def _unavailable_factory(
    provider_id: str,
    *,
    message: str,
    install_hint: str,
) -> ProviderFactory:
    def factory(**_: Any) -> SkeletonProvider:
        raise ProviderUnavailableError(
            provider_id,
            message,
            install_hint=install_hint,
        )

    return factory


_REGISTRATIONS: dict[str, ProviderRegistration] = {
    "simscape-json": ProviderRegistration(
        provider_id="simscape-json",
        metadata=ProviderMetadata(
            name="Simscape JSON",
            engine="simscape-json",
            capabilities=("physics", "file", "fallback"),
        ),
        factory=_json_factory,
    ),
    "simscape-live": ProviderRegistration(
        provider_id="simscape-live",
        metadata=ProviderMetadata(
            name="Simscape Live",
            engine="simscape-live",
            capabilities=("physics", "live"),
        ),
        factory=_unavailable_factory(
            "simscape-live",
            message="live Simscape provider is not implemented in core-only mode",
            install_hint="use simscape-json or install/configure MATLAB bridge support",
        ),
    ),
    "mujoco": ProviderRegistration(
        provider_id="mujoco",
        metadata=ProviderMetadata(
            name="MuJoCo",
            engine="mujoco",
            capabilities=("physics", "native-fk"),
        ),
        factory=_load_factory(
            "mujoco",
            "src.tools.starting_pose_matcher.providers.mujoco",
            install_hint="pip install mujoco",
        ),
    ),
    "drake": ProviderRegistration(
        provider_id="drake",
        metadata=ProviderMetadata(
            name="Drake",
            engine="drake",
            capabilities=("physics", "native-fk"),
        ),
        factory=_load_factory(
            "drake",
            "src.tools.starting_pose_matcher.providers.drake",
            install_hint="pip install drake",
        ),
    ),
    "pinocchio": ProviderRegistration(
        provider_id="pinocchio",
        metadata=ProviderMetadata(
            name="Pinocchio",
            engine="pinocchio",
            capabilities=("physics", "native-fk"),
        ),
        factory=_load_factory(
            "pinocchio",
            "src.tools.starting_pose_matcher.providers.pinocchio",
            install_hint="pip install pinocchio",
        ),
    ),
    "opensim": ProviderRegistration(
        provider_id="opensim",
        metadata=ProviderMetadata(
            name="OpenSim",
            engine="opensim",
            capabilities=("physics", "native-fk"),
        ),
        factory=_load_factory(
            "opensim",
            "src.tools.starting_pose_matcher.providers.opensim",
            install_hint="pip install opensim",
        ),
    ),
    "openpose": ProviderRegistration(
        provider_id="openpose",
        metadata=ProviderMetadata(
            name="OpenPose",
            engine="openpose",
            capabilities=("observation", "json"),
        ),
        factory=_load_factory(
            "openpose",
            "src.tools.starting_pose_matcher.providers.openpose",
            install_hint="provide OpenPose JSON output",
        ),
    ),
    "mediapipe": ProviderRegistration(
        provider_id="mediapipe",
        metadata=ProviderMetadata(
            name="MediaPipe",
            engine="mediapipe",
            capabilities=("observation", "landmarks"),
        ),
        factory=_load_factory(
            "mediapipe",
            "src.tools.starting_pose_matcher.providers.mediapipe",
            install_hint="provide MediaPipe landmark data",
        ),
    ),
}


def list_provider_ids() -> list[str]:
    """Return stable provider IDs in registry order."""

    return list(_REGISTRATIONS)


def get_registration(provider_id: str) -> ProviderRegistration:
    """Return registration metadata for ``provider_id``."""

    try:
        return _REGISTRATIONS[provider_id]
    except KeyError as exc:
        raise UnknownProviderError(provider_id) from exc


def list_provider_metadata() -> dict[str, ProviderMetadata]:
    """Return serializable metadata for all registered providers."""

    return {
        provider_id: registration.metadata
        for provider_id, registration in _REGISTRATIONS.items()
    }


def create_provider(provider_id: str, **kwargs: Any) -> SkeletonProvider:
    """Create a provider by stable ID using the provider's lazy factory."""

    return get_registration(provider_id).factory(**kwargs)


__all__ = [
    "ProviderFactory",
    "ProviderRegistration",
    "create_provider",
    "get_registration",
    "list_provider_ids",
    "list_provider_metadata",
]
