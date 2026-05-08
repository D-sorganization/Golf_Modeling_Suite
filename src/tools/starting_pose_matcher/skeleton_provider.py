"""Backwards-compatibility shim.

The original ``skeleton_provider`` module hosted both the abstract
``SkeletonProvider`` base class and the ``JsonSkeletonProvider``
implementation.  As of issue #4388 / #4367 the providers live in the
``providers/`` subpackage so each engine adapter (Simscape, MuJoCo,
Drake, Pinocchio, OpenSim) lives in its own file with its own optional
import.

This module re-exports the public surface so any existing import like::

    from src.tools.starting_pose_matcher.skeleton_provider import (
        SkeletonProvider, JsonSkeletonProvider, fallback_skeleton,
    )

keeps working.
"""

from __future__ import annotations

from src.tools.starting_pose_matcher.core import fallback_skeleton  # noqa: F401
from src.tools.starting_pose_matcher.providers import (  # noqa: F401
    PROVIDER_REGISTRY,
    ProviderUnavailable,
    SkeletonProvider,
    SimscapeJsonSkeletonProvider as JsonSkeletonProvider,
    available_providers,
    get_provider,
)

__all__ = [
    "PROVIDER_REGISTRY",
    "ProviderUnavailable",
    "SkeletonProvider",
    "JsonSkeletonProvider",
    "available_providers",
    "fallback_skeleton",
    "get_provider",
]
