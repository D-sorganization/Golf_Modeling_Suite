"""Shared dashboard package.

Exports the launcher entry point and the primary dashboard window used by all
physics-engine launchers in the fleet.
"""

from .launcher import launch_dashboard
from .window import UnifiedDashboardWindow

__all__ = [
    "UnifiedDashboardWindow",
    "launch_dashboard",
]
<<<<<<< HEAD
=======


def __getattr__(name: str) -> Any:
    if name == "launch_dashboard":
        from .launcher import launch_dashboard as _fn

        return _fn
    if name == "UnifiedDashboardWindow":
        from .window import UnifiedDashboardWindow as _cls

        return _cls
    raise AttributeError(
        f"module 'src.shared.python.dashboard' has no attribute {name!r}"
    )


if TYPE_CHECKING:
    from .launcher import launch_dashboard
    from .window import UnifiedDashboardWindow
>>>>>>> origin/main
