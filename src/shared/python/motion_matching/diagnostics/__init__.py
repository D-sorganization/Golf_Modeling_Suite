"""Diagnostic utilities for the GolfSwing3D model input MAT files.

These tools live outside MATLAB/Simscape and provide a fast, dependency-light
way to inspect joint-angle inputs (from CSV or model-workspace dumps), compute
a coarse forward-kinematics skeleton, and flag values that disagree with a
reference golfer pose. They are NOT a replacement for Simscape; they exist to
diagnose 'doesn't look right' reports without spinning up MATLAB.
"""

from .forward_kinematics import (
    SegmentLengths,
    SkeletonPose,
    forward_kinematics,
)
from .reference_pose import (
    REFERENCE_GOLFER_FIELDS,
    compare_to_reference,
    reference_golfer_setup,
)

__all__ = [
    "REFERENCE_GOLFER_FIELDS",
    "SegmentLengths",
    "SkeletonPose",
    "compare_to_reference",
    "forward_kinematics",
    "reference_golfer_setup",
]
