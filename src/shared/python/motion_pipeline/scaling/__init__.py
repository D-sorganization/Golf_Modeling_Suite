"""
Anthropometric scaling for motion capture pipeline.

Part of issue #4565. Scales a generic SkeletonRig to match subject-specific
marker data using segment length estimation.
"""

from .anthropometric import MarkerMap, get_marker_map, scale_skeleton
from .marker_maps import IOR, PLUG_IN_GAIT, THEIA, VICON_FULL_BODY, MarkerSet
from .opensim_scale import OpenSimScaleBackend

__all__ = [
    "scale_skeleton",
    "MarkerMap",
    "get_marker_map",
    "MarkerSet",
    "PLUG_IN_GAIT",
    "IOR",
    "THEIA",
    "VICON_FULL_BODY",
    "OpenSimScaleBackend",
]
