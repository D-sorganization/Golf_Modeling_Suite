"""Starting-pose matcher: align Simscape golfer skeleton to mocap targets.

This package provides tools for aligning a Simscape multibody golfer model
to motion-capture data by solving for a 7-DOF rigid transform (translation,
rotation, scale) that minimizes the error between model and mocap skeletons.

The package has been relocated from::

    src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/

to this canonical location under ``src/tools/``. A deprecation shim remains
at the old path that redirects to this package.

Example::

    python -m src.tools.starting_pose_matcher

Or launch from the unified launcher tile "Starting Pose Matcher".
"""

from .core import (
    CM_TO_M,
    DEFAULT_EVENT_PRESET,
    DEFAULT_PHASE,
    EVENT_KEYS,
    EVENT_LABEL_PRESETS,
    MocapEvents,
    PHASE_BOUNDS,
    PHASE_KEYS,
    PoseSlot,
    RigidTransform,
    SESSION_SCHEMA_VERSION,
    Skeleton,
    SkeletonTrajectory,
    load_mocap_xlsx,
    load_simscape_trajectory_csv,
    load_skeleton,
    phase_display_label,
    phase_key_from_label,
)

__all__ = [
    "CM_TO_M",
    "DEFAULT_EVENT_PRESET",
    "DEFAULT_PHASE",
    "EVENT_KEYS",
    "EVENT_LABEL_PRESETS",
    "MocapEvents",
    "PHASE_BOUNDS",
    "PHASE_KEYS",
    "PoseSlot",
    "RigidTransform",
    "SESSION_SCHEMA_VERSION",
    "Skeleton",
    "SkeletonTrajectory",
    "load_mocap_xlsx",
    "load_simscape_trajectory_csv",
    "load_skeleton",
    "phase_display_label",
    "phase_key_from_label",
]