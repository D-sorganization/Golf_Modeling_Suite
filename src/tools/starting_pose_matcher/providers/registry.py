"""Lazy provider registry for starting-pose matcher skeleton sources."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.tools.starting_pose_matcher.skeleton_provider import (
    ProviderConfigurationError,
    ProviderMetadata,
    ProviderUnavailableError,
    SkeletonProvider,
)

ProviderFactory = Callable[..., SkeletonProvider]

PROVIDER_IDS: tuple[str, ...] = (
    "simscape-json",
    "simscape-live",
    "mujoco",
    "drake",
    "pinocchio",
    "opensim",
    "openpose",
    "mediapipe",
)

_METADATA: dict[str, ProviderMetadata] = {
    "simscape-json": ProviderMetadata(
        name="simscape-json",
        engine="simscape",
        capabilities=("skeleton", "json", "fallback"),
    ),
    "simscape-live": ProviderMetadata(
        name="simscape-live",
        engine="simscape",
        capabilities=("skeleton", "live"),
    ),
    "mujoco": ProviderMetadata(name="mujoco", engine="mujoco"),
    "drake": ProviderMetadata(name="drake", engine="drake"),
    "pinocchio": ProviderMetadata(name="pinocchio", engine="pinocchio"),
    "opensim": ProviderMetadata(name="opensim", engine="opensim"),
    "openpose": ProviderMetadata(
        name="openpose",
        engine="openpose",
        capabilities=("observed-target",),
    ),
    "mediapipe": ProviderMetadata(
        name="mediapipe",
        engine="mediapipe",
        capabilities=("observed-target",),
    ),
}


def _create_simscape_json(**config: Any) -> SkeletonProvider:
    from src.tools.starting_pose_matcher.providers.simscape_json import (
        DEFAULT_POSES,
        SimscapeJsonSkeletonProvider,
    )

    default_dir = Path(__file__).resolve().parent.parent
    json_dir = Path(config.get("json_dir") or default_dir)
    poses = tuple(config.get("poses") or DEFAULT_POSES)
    return SimscapeJsonSkeletonProvider(json_dir=json_dir, poses=poses)


def _unavailable_factory(provider_id: str, install_hint: str) -> ProviderFactory:
    def _factory(**_config: Any) -> SkeletonProvider:
        raise ProviderUnavailableError(
            provider_id,
            "provider backend is not implemented in this foundation slice",
            install_hint=install_hint,
        )

    return _factory


_FACTORIES: dict[str, ProviderFactory] = {
    "simscape-json": _create_simscape_json,
    "simscape-live": _unavailable_factory(
        "simscape-live",
        "Use 'simscape-json' until the live MATLAB bridge provider is added.",
    ),
    "mujoco": _unavailable_factory(
        "mujoco",
        "Install and wire the MuJoCo provider in a backend-specific slice.",
    ),
    "drake": _unavailable_factory(
        "drake",
        "Install and wire the Drake provider in a backend-specific slice.",
    ),
    "pinocchio": _unavailable_factory(
        "pinocchio",
        "Install and wire the Pinocchio provider in a backend-specific slice.",
    ),
    "opensim": _unavailable_factory(
        "opensim",
        "Install and wire the OpenSim provider in a backend-specific slice.",
    ),
    "openpose": _unavailable_factory(
        "openpose",
        "Wire the OpenPose observation provider in a target-loader slice.",
    ),
    "mediapipe": _unavailable_factory(
        "mediapipe",
        "Wire the MediaPipe observation provider in a target-loader slice.",
    ),
}


def provider_metadata(provider_id: str) -> ProviderMetadata:
    """Return static metadata without importing provider backends."""
    try:
        return _METADATA[provider_id]
    except KeyError as exc:
        known = ", ".join(PROVIDER_IDS)
        raise ProviderConfigurationError(
            f"Unknown provider '{provider_id}'. Known providers: {known}"
        ) from exc


def create_provider(provider_id: str, **config: Any) -> SkeletonProvider:
    """Create a provider by stable ID using lazy factories."""
    try:
        factory = _FACTORIES[provider_id]
    except KeyError as exc:
        known = ", ".join(PROVIDER_IDS)
        raise ProviderConfigurationError(
            f"Unknown provider '{provider_id}'. Known providers: {known}"
        ) from exc
    return factory(**config)
