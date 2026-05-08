"""Runtime registry of :class:`FitSwingProvider` implementations.

Engines call :func:`register_provider` at import time so the matcher can
discover them via :func:`available_engines` and dispatch by name through
:func:`get_provider`.

Registration is idempotent: registering the same provider instance (or a
provider with the same ``engine_name``) twice is a no-op with a debug log.

The :func:`unregister_provider` hook exists for tests; production code
should not call it.
"""

from __future__ import annotations

import logging

from .fit_swing import FitSwingProvider

__all__ = [
    "available_engines",
    "get_provider",
    "register_provider",
    "unregister_provider",
]

_LOGGER = logging.getLogger(__name__)
_REGISTRY: dict[str, FitSwingProvider] = {}


def register_provider(provider: FitSwingProvider) -> None:
    """Register ``provider`` under its ``engine_name``.

    Idempotent: if a provider with the same ``engine_name`` is already
    registered, this is a no-op (debug-logged). To replace, call
    :func:`unregister_provider` first.

    Raises:
        TypeError: if ``provider`` does not satisfy
            :class:`FitSwingProvider` at runtime.
        ValueError: if ``provider.engine_name`` is empty or non-string.
    """
    if not isinstance(provider, FitSwingProvider):
        raise TypeError(
            f"register_provider requires a FitSwingProvider; got {type(provider)!r}"
        )
    name = getattr(provider, "engine_name", None)
    if not isinstance(name, str) or not name:
        raise ValueError(
            f"Provider.engine_name must be a non-empty string; got {name!r}"
        )
    if name in _REGISTRY:
        _LOGGER.debug(
            "Provider %r already registered; ignoring duplicate registration",
            name,
        )
        return
    _REGISTRY[name] = provider


def get_provider(engine_name: str) -> FitSwingProvider:
    """Return the provider registered under ``engine_name``.

    Raises:
        KeyError: if no provider is registered under that name. The error
            message lists the currently available engines.
    """
    if engine_name not in _REGISTRY:
        available = sorted(_REGISTRY.keys())
        raise KeyError(
            f"No FitSwingProvider registered for engine_name={engine_name!r}. "
            f"Available engines: {available!r}"
        )
    return _REGISTRY[engine_name]


def available_engines() -> list[str]:
    """Return the sorted list of currently registered engine names."""
    return sorted(_REGISTRY.keys())


def unregister_provider(engine_name: str) -> None:
    """Remove ``engine_name`` from the registry (test hook).

    No-op if the name is not registered.
    """
    _REGISTRY.pop(engine_name, None)
