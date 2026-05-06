"""Motion-matching diagnostics.

Public entry points:

- :func:`compare_clubhead_traces` — numeric report comparing two ``ClubTarget``s,
  with renderers ``plot_3d_overlay``, ``plot_per_axis_timeseries``,
  ``plot_speed_comparison``, ``plot_setup_pose_skeletons``.
- :func:`forward_kinematics` — minimal Python FK over the model's joint
  hierarchy. Not a Simscape replacement; for fast input-MAT inspection.
- :func:`reference_golfer_setup` / :func:`compare_to_reference` — codified
  "credible golfer setup" pose for sanity-checking input MATs.

See ``docs/golf-model/INPUT_POSE_INVESTIGATION.md`` for the design context.
"""

from __future__ import annotations

from .clubhead_trace import (
    TraceCompareOptions,
    TraceCompareReport,
    compare_clubhead_traces,
    plot_3d_overlay,
    plot_per_axis_timeseries,
    plot_setup_pose_skeletons,
    plot_speed_comparison,
)
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
    "TraceCompareOptions",
    "TraceCompareReport",
    "compare_clubhead_traces",
    "compare_to_reference",
    "forward_kinematics",
    "plot_3d_overlay",
    "plot_per_axis_timeseries",
    "plot_setup_pose_skeletons",
    "plot_speed_comparison",
    "reference_golfer_setup",
]
