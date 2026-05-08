"""Skeleton-provider package for the starting-pose matcher.

A ``SkeletonProvider`` is the seam that lets the matcher work with any
of the project's physics engines (Simscape, MuJoCo, Drake, Pinocchio,
OpenSim) without each provider's import being a load-time dependency.

The provider contract (per issue #4388 / #4367) is::

    class SkeletonProvider(ABC):
        engine_name: ClassVar[str]            # e.g. "MuJoCo"
        @classmethod
        def is_available(cls) -> bool:        # is the engine importable?
        def list_poses(self) -> list[str]:    # which poses can I produce?
        def get_skeleton(self, pose) -> Skeleton

Each engine's adapter lives in a sibling submodule and **MUST NOT**
import the engine library at module level — instead, the engine import
goes inside ``is_available()`` and the methods that need it.  This
keeps the package importable in environments missing 3 of the 4
optional engines.

The registry returns the FIRST AVAILABLE provider for a given engine
name, or raises :class:`ProviderUnavailable` so callers can fall back
to a JSON skeleton or the FK-derived default.

Public API:

    PROVIDER_REGISTRY        list[type[SkeletonProvider]] (in priority order)
    available_providers()    -> list[type[SkeletonProvider]] currently importable
    get_provider(name, **kw) -> SkeletonProvider
    ProviderUnavailable      exception type
    SkeletonProvider         abstract base class

The Simscape JSON provider always lives at the head of the registry
because the existing matcher pipeline (fit_swing_full_pipeline.m,
solve_starting_pose.m) consumes its output directly.
"""

from __future__ import annotations

from ._base import ProviderUnavailable, SkeletonProvider
from .simscape_json import SimscapeJsonSkeletonProvider

# Each engine submodule is imported defensively — its top-level body
# does NOT touch the engine library, so a missing pydrake / mujoco
# wheel does not break this package's import.
from . import mujoco_provider, drake_provider, pinocchio_provider, opensim_provider  # noqa: F401

PROVIDER_REGISTRY: list[type[SkeletonProvider]] = [
    SimscapeJsonSkeletonProvider,
    mujoco_provider.MujocoSkeletonProvider,
    drake_provider.DrakeSkeletonProvider,
    pinocchio_provider.PinocchioSkeletonProvider,
    opensim_provider.OpenSimSkeletonProvider,
]


def available_providers() -> list[type[SkeletonProvider]]:
    """Return the subset of providers whose engine is importable now."""
    return [p for p in PROVIDER_REGISTRY if p.is_available()]


def get_provider(engine_name: str, **kwargs) -> SkeletonProvider:
    """Construct the provider whose ``engine_name`` matches.

    Args:
        engine_name: e.g. ``"Simscape"``, ``"MuJoCo"``, ``"Drake"``,
            ``"Pinocchio"``, ``"OpenSim"`` (case-insensitive).
        **kwargs: forwarded to the provider's constructor.

    Raises:
        ProviderUnavailable: the engine isn't installed in this env.
        KeyError: no provider with that name.
    """
    target = engine_name.strip().lower()
    for cls in PROVIDER_REGISTRY:
        if cls.engine_name.lower() == target:
            if not cls.is_available():
                raise ProviderUnavailable(
                    f"{cls.engine_name} skeleton provider unavailable: "
                    "the engine library isn't importable in this env.")
            return cls(**kwargs)
    raise KeyError(f"No SkeletonProvider for engine {engine_name!r}.  "
                   f"Known: {[p.engine_name for p in PROVIDER_REGISTRY]}")


__all__ = [
    "PROVIDER_REGISTRY",
    "ProviderUnavailable",
    "SkeletonProvider",
    "SimscapeJsonSkeletonProvider",
    "available_providers",
    "get_provider",
]
