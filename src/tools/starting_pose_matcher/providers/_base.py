"""Abstract base for cross-engine skeleton providers.

The matcher's :class:`PoseSlot` carries one ``Skeleton`` per pose name.
A :class:`SkeletonProvider` knows how to compute that skeleton from an
engine-native model (URDF, MJCF, OSIM, Simscape JSON, …) given a
named pose.

Every provider implementation MUST:

1. Set ``engine_name`` (class-level, lowercase recommended).
2. Implement ``is_available()`` as a class method that returns ``True``
   only when the engine library is importable in this environment.
   ``is_available`` MUST NOT raise — wrap the import in try/except.
3. Implement ``list_poses()`` and ``get_skeleton(pose_name)``.
4. Return :class:`Skeleton` objects whose ``joints`` dict uses the
   matcher's compact short names::

       hip, spine, torso, hub, ls, rs, le, re, lw, rw, mp, ch

   Engine-specific joint name maps live in each provider's submodule.

Providers are deliberately permitted to fall back to the FK-derived
default skeleton when their engine model lacks a particular pose
(e.g. an URDF doesn't include "TopofBackswing"), so the matcher keeps
showing a body even when only the "Address" pose is plumbed through.

The :class:`ProviderUnavailable` exception is raised by ``get_provider``
when a caller asks for an engine whose library isn't installed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from src.tools.starting_pose_matcher.core import Skeleton


class ProviderUnavailable(RuntimeError):
    """Raised when a requested engine adapter can't import its engine."""


class SkeletonProvider(ABC):
    """Abstract source of named skeleton poses for one physics engine."""

    #: Public engine name shown in the GUI, e.g. ``"Simscape"``.
    engine_name: ClassVar[str] = "abstract"

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if the engine library can be imported right now."""

    @abstractmethod
    def list_poses(self) -> list[str]:
        """Names of poses this provider can produce (e.g. Address, Impact)."""

    @abstractmethod
    def get_skeleton(self, pose_name: str) -> Skeleton:
        """Return the :class:`Skeleton` for ``pose_name``.

        May raise :class:`KeyError` for unknown poses or fall back to a
        default skeleton — implementations document their behaviour.
        """

    # Convenience: a default __repr__ that's helpful in tests + the GUI.
    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        try:
            poses = ", ".join(self.list_poses())
        except Exception:  # noqa: BLE001
            poses = "?"
        return f"<{self.__class__.__name__}({self.engine_name}) poses=[{poses}]>"


__all__ = ["ProviderUnavailable", "SkeletonProvider"]
