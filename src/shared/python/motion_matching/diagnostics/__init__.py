"""Diagnostics for the motion-matching pipeline.

Currently exposes :mod:`initial_state_diff`, which compares the pose
specified in a Simscape input MAT file against the pose the constraint
solver actually settles to at ``t=0`` (loop-closure projection).
"""

from __future__ import annotations

from .initial_state_diff import (
    InitialStateDiffReport,
    load_diff_report,
    plot_cartesian_delta_summary,
    plot_per_joint_delta_bars,
    plot_skeleton_overlay,
    summarize_for_pr_comment,
)

__all__ = [
    "InitialStateDiffReport",
    "load_diff_report",
    "plot_cartesian_delta_summary",
    "plot_per_joint_delta_bars",
    "plot_skeleton_overlay",
    "summarize_for_pr_comment",
]
