"""Shared dashboard package.

Exports the launcher entry point and the primary dashboard window used by all
physics-engine launchers in the fleet.
"""

def __getattr__(name: str):
    if name == "launch_dashboard":
        from .launcher import launch_dashboard
        return launch_dashboard
    if name == "UnifiedDashboardWindow":
        from .window import UnifiedDashboardWindow
        return UnifiedDashboardWindow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "UnifiedDashboardWindow",
    "launch_dashboard",
]
