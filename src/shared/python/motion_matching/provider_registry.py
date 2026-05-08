"""Provider registry for motion matching engines.

Auto-discovery of FitSwingProvider implementations across physics engines.
Each engine module's __init__.py calls register_provider() at import time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fit_swing import FitSwingProvider

# Internal registry: engine_name -> provider instance
_providers: dict[str, FitSwingProvider] = {}


def register_provider(provider: FitSwingProvider) -> None:
    """Register a FitSwingProvider implementation.

    Args:
        provider: A FitSwingProvider instance to register.

    Raises:
        ValueError: If a provider with the same engine_name is already registered.
    """
    from .fit_swing import FitSwingProvider

    if not isinstance(provider, FitSwingProvider):
        raise TypeError(
            f"Provider must implement FitSwingProvider, got {type(provider)}"
        )

    engine_name = provider.engine_name
    if engine_name in _providers:
        raise ValueError(
            f"Provider for engine {engine_name!r} already registered. "
            "Use unregister_provider() first if replacing."
        )
    _providers[engine_name] = provider


def unregister_provider(engine_name: str) -> None:
    """Unregister a provider by engine name.

    Args:
        engine_name: The engine name to unregister.

    Raises:
        KeyError: If no provider is registered for the given engine name.
    """
    if engine_name not in _providers:
        raise KeyError(f"No provider registered for engine {engine_name!r}")
    del _providers[engine_name]


def get_provider(engine_name: str) -> FitSwingProvider:
    """Get a registered provider by engine name.

    Args:
        engine_name: The engine name to look up.

    Returns:
        The registered FitSwingProvider for the engine.

    Raises:
        KeyError: If no provider is registered for the given engine name.
    """
    if engine_name not in _providers:
        available = list(_providers.keys())
        raise KeyError(
            f"No provider registered for engine {engine_name!r}. "
            f"Available engines: {available}"
        )
    return _providers[engine_name]


def available_engines() -> list[str]:
    """List all registered engine names.

    Returns:
        Sorted list of engine names with registered providers.
    """
    return sorted(_providers.keys())


def clear_providers() -> None:
    """Clear all registered providers.

    Primarily useful for testing. In production, providers are registered
    once at module import time.
    """
    _providers.clear()


def discover_providers() -> list[str]:
    """Discover and register providers from engine modules.

    Walks src.engines.physics_engines.*.python.motion_matching packages
    and imports them to trigger provider registration.

    Returns:
        List of engine names that were successfully discovered.
    """
    import importlib
    import pkgutil

    discovered: list[str] = []

    try:
        import src.engines.physics_engines as physics_pkg
    except ImportError:
        return discovered

    physics_path = physics_pkg.__path__
    for _, engine_name, is_pkg in pkgutil.iter_modules(physics_path):
        if not is_pkg:
            continue

        motion_matching_path = f"src.engines.physics_engines.{engine_name}.python.motion_matching"
        try:
            importlib.import_module(motion_matching_path)
            if engine_name in available_engines():
                discovered.append(engine_name)
        except ImportError:
            # Engine doesn't have motion_matching module - that's OK
            pass

    return discovered