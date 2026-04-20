"""Shared dashboard package.

Exports the launcher entry point and the primary dashboard window used by all
physics-engine launchers in the fleet.

Imports are lazy (PEP 562 ``__getattr__``) so that headless code paths — in
particular the FastAPI server's import chain — can load this package without
pulling in PyQt6. Consumers that actually dereference ``launch_dashboard`` or
``UnifiedDashboardWindow`` pay the GUI import cost the first time only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = [
    "UnifiedDashboardWindow",
    "launch_dashboard",
]


def __getattr__(name: str) -> Any:
    if name == "launch_dashboard":
        from .launcher import launch_dashboard as _fn

        return _fn
    if name == "UnifiedDashboardWindow":
        from .window import UnifiedDashboardWindow as _cls

        return _cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from .launcher import launch_dashboard
    from .window import UnifiedDashboardWindow
