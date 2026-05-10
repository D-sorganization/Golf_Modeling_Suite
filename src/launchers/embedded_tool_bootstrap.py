"""Bootstrap registration of embeddable tools for the launcher.

This module imports and registers all embeddable tools at launcher startup,
ensuring the EMBEDDABLE_TOOL_REGISTRY is populated before any context menus
or embedded host widgets are created.

Part of EPIC #4993 (Subtask 5) - addresses review feedback from #5049.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.python.logging_pkg.logging_config import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Registry state tracking
_bootstrap_complete = False
_registered_tools: list[str] = []


def bootstrap_embeddable_tools() -> list[str]:
    """Import and register all embeddable tools.

    This function performs lazy imports of tool adapter modules, which
    triggers their self-registration with the EMBEDDABLE_TOOL_REGISTRY.

    Returns:
        List of tool_ids that were registered

    Note:
        This function is idempotent - calling it multiple times is safe.
        Subsequent calls return the list of previously registered tools.
    """
    global _bootstrap_complete, _registered_tools

    if _bootstrap_complete:
        return _registered_tools

    # List of tool packages whose __init__.py self-registers on import.
    # Each package's __init__.py calls register_embeddable_tool() behind a
    # contextlib.suppress(ImportError) guard so optional engine wheels
    # (mujoco, drake, pinocchio, opensim, myosuite, etc.) failing to load
    # is a soft skip rather than a launcher startup error.
    adapter_modules = [
        "src.tools.pose_studio",
        "src.tools.data_explorer",
        "src.tools.model_explorer",
        "src.tools.starting_pose_matcher",
        "src.tools.pose_subscriber_demo",
        "src.engines.physics_engines.mujoco.python.mujoco_humanoid_golf",
        "src.engines.physics_engines.drake.python.src",
        "src.engines.physics_engines.pinocchio.python.pinocchio_golf",
        "src.engines.physics_engines.opensim.python",
        "src.engines.physics_engines.myosuite.python",
        "src.engines.Simscape_Multibody_Models.3D_Golf_Model.python.src.apps",
    ]

    registered = []
    for module_path in adapter_modules:
        try:
            # Import the module - it self-registers at module level
            __import__(module_path)
            # Track by last segment of the dotted path
            tool_id = module_path.split(".")[-1].replace("_embed_adapter", "")
            registered.append(tool_id)
            logger.debug(f"Bootstrapped embeddable tool: {tool_id}")
        except (ImportError, ModuleNotFoundError) as e:
            # Tools may have optional dependencies (PyQt6, optional engine
            # wheels, etc.). Log at debug — a missing optional engine is
            # not a launcher-level failure.
            logger.debug(f"embed bootstrap skipped {module_path}: {e}")
        except Exception:  # noqa: BLE001
            # Catch any other unexpected errors during registration
            logger.exception(f"embed bootstrap failed for {module_path}")

    _registered_tools = registered
    _bootstrap_complete = True

    logger.info(f"Bootstrapped {len(registered)} embeddable tools: {registered}")
    return registered


def get_bootstrapped_tools() -> list[str]:
    """Return list of tool_ids that were bootstrapped.

    Returns:
        List of registered tool_ids, or empty list if bootstrap not yet run
    """
    return _registered_tools.copy()


def reset_bootstrap_state() -> None:
    """Reset bootstrap state (for testing only).

    Warning:
        This function is intended for test fixtures only. Calling this
        during normal operation will break embedded tool functionality.
    """
    global _bootstrap_complete, _registered_tools
    _bootstrap_complete = False
    _registered_tools = []
