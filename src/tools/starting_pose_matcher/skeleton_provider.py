"""Pluggable source of model skeleton joint positions.

The matcher's GUI talks to a ``SkeletonProvider``: each provider knows
how to enumerate model poses and return their joint positions in the
matcher's compact vocabulary (``hip``, ``spine``, ``torso``, ``hub``,
``ls``, ``rs``, ``le``, ``re``, ``lw``, ``rw``, ``mp``, ``ch``).

Concrete providers live under ``src.tools.starting_pose_matcher.providers``.
The legacy ``JsonSkeletonProvider`` import remains as a compatibility
alias for the first-class Simscape JSON provider.
"""

from __future__ import annotations

from typing import Protocol

from src.tools.starting_pose_matcher.core import (
    Skeleton,
    fallback_skeleton,
)


class SkeletonProvider(Protocol):
    """Structural interface for sources of model skeleton poses."""

    def list_poses(self) -> list[str]:
        """Return the names of the poses this provider can produce."""
        ...

    def get_skeleton(self, pose_name: str) -> Skeleton:
        """Return the :class:`Skeleton` for the named pose."""
        ...


from src.tools.starting_pose_matcher.providers.simscape import (  # noqa: E402
    SimscapeJsonProvider,
    SimscapeJsonProviderError,
    SimscapeProviderError,
)

JsonSkeletonProvider = SimscapeJsonProvider

__all__ = [
    "JsonSkeletonProvider",
    "SimscapeJsonProvider",
    "SimscapeJsonProviderError",
    "SimscapeProviderError",
    "SkeletonProvider",
    "fallback_skeleton",
]
