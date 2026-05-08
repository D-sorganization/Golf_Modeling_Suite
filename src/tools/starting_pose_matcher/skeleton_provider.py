"""Skeleton provider abstraction for the starting-pose matcher.

This module provides a `SkeletonProvider` protocol that allows the
starting-pose matcher to work with different skeleton formats:
- Simscape JSON (current)
- MuJoCo MJCF
- Drake URDF/SDF
- Pinocchio model

Future extension point for issue #4367.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from .core import Skeleton


class SkeletonProvider(ABC):
    """Abstract base class for skeleton data providers.

    Implement this class to load skeletons from different formats
    (Simscape JSON, MuJoCo MJCF, Drake URDF, etc.).
    """

    @abstractmethod
    def load_skeleton(self, source: str | Path, pose_name: str) -> Skeleton:
        """Load a skeleton from the given source.

        Parameters
        ----------
        source : str | Path
            Path to the skeleton source file or directory.
        pose_name : str
            Name of the pose to load (e.g., "TopofBackswing", "Impact").

        Returns
        -------
        Skeleton
            The loaded skeleton with joints and segments.
        """
        pass

    @abstractmethod
    def get_joint_names(self) -> list[str]:
        """Return list of joint names in the skeleton."""
        pass

    @abstractmethod
    def get_default_pose(self) -> dict[str, float]:
        """Return default joint angles for this skeleton."""
        pass


class SimscapeSkeletonProvider(SkeletonProvider):
    """Load skeletons from Simscape JSON format.

    This is the current format used by the starting-pose matcher.
    Skeletons are exported from MATLAB via export_default_skeleton.m
    and stored as JSON files.
    """

    def __init__(self) -> None:
        self._joint_names: list[str] = []
        self._default_pose: dict[str, float] = {}

    def load_skeleton(self, source: str | Path, pose_name: str) -> Skeleton:
        """Load a skeleton from Simscape JSON format.

        Parameters
        ----------
        source : str | Path
            Path to the JSON file (e.g., simscape_skeleton_TopofBackswing.json).
        pose_name : str
            Name of the pose (used for labeling).

        Returns
        -------
        Skeleton
            The loaded skeleton.
        """
        from .core import load_skeleton
        return load_skeleton(Path(source), pose_name)

    def get_joint_names(self) -> list[str]:
        """Return list of joint names in the Simscape skeleton."""
        # Standard Simscape golf skeleton joints
        return [
            "pelvis", "spine", "torso", "hub",
            "ls", "rs",  # left/right shoulder
            "le", "re",  # left/right elbow
            "lw", "rw",  # left/right wrist
            "lh", "rh",  # left/right hand
            "mp",  # mid-point (hands)
            "ch",  # clubhead
        ]

    def get_default_pose(self) -> dict[str, float]:
        """Return default address pose joint angles."""
        from .core import reference_golfer_setup
        try:
            return reference_golfer_setup()
        except ImportError:
            # Fallback if reference_golfer_setup is not available
            return {
                "HipX": 0.0, "HipY": 0.0, "HipZ": 0.0,
                "SpineX": 0.0, "SpineY": 0.0,
                "Torso": 0.0,
                "LScapX": 0.0, "LScapY": 0.0,
                "RScapX": 0.0, "RScapY": 0.0,
                "LSX": 0.0, "LSY": 0.0, "LSZ": 0.0,
                "RSX": 0.0, "RSY": 0.0, "RSZ": 0.0,
                "LEX": 0.0, "LEY": 0.0,
                "REX": 0.0, "REY": 0.0,
                "LWX": 0.0, "LWY": 0.0,
                "RWX": 0.0, "RWY": 0.0,
            }


# Future providers can be added here:
# - MuJoCoSkeletonProvider
# - DrakeSkeletonProvider
# - PinocchioSkeletonProvider