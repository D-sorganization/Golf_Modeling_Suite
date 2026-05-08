"""Lazy provider registry for the starting-pose matcher."""

from src.tools.starting_pose_matcher.providers.registry import (
    PROVIDER_IDS,
    create_provider,
    provider_metadata,
)
from src.tools.starting_pose_matcher.providers.simscape_json import (
    SimscapeJsonSkeletonProvider,
)

__all__ = [
    "PROVIDER_IDS",
    "SimscapeJsonSkeletonProvider",
    "create_provider",
    "provider_metadata",
]
