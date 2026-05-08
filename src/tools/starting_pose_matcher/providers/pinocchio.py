"""Pinocchio skeleton provider for starting-pose matcher.

This module provides a Pinocchio-based skeleton provider that maps Pinocchio
model frames/joints to the shared matcher skeleton vocabulary.

Required vocabulary:
    hip, spine, torso, hub, ls, rs, le, re, lw, rw, mp, ch
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import defusedxml.ElementTree as ElementTree

from src.tools.starting_pose_matcher.skeleton_provider import ProviderMetadata

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# Frame/joint name mapping from Pinocchio to matcher vocabulary
# These are the standard names expected by the starting-pose matcher
PINOCCHIO_TO_MATCHER_VOCAB: dict[str, str] = {
    # Lower body
    "hip": "hip",
    "pelvis": "hip",
    # Spine
    "spine": "spine",
    "torso": "torso",
    # Upper body
    "hub": "hub",
    # Shoulders
    "left_shoulder": "ls",
    "right_shoulder": "rs",
    # Elbows
    "left_elbow": "le",
    "right_elbow": "re",
    # Wrists/Hands
    "left_wrist": "lw",
    "right_wrist": "rw",
    # Mid-point (between hands)
    "midpoint": "mp",
    # Clubhead
    "clubhead": "ch",
}

# Canonical lookup names for required matcher vocabulary.
MATCHER_TO_PINOCCHIO: dict[str, str] = {
    "hip": "hip",
    "spine": "spine",
    "torso": "torso",
    "hub": "hub",
    "ls": "left_shoulder",
    "rs": "right_shoulder",
    "le": "left_elbow",
    "re": "right_elbow",
    "lw": "left_wrist",
    "rw": "right_wrist",
    "mp": "midpoint",
    "ch": "clubhead",
}


class PinocchioNotAvailableError(Exception):
    """Raised when Pinocchio is not installed but a Pinocchio provider is requested."""


class PinocchioProviderError(Exception):
    """Raised when there's an error with the Pinocchio provider configuration."""


class PinocchioSkeletonProvider:
    """Provides skeleton data from a Pinocchio model.

    This provider loads a Pinocchio URDF model and extracts frame/joint
    positions to map them to the shared matcher skeleton vocabulary.

    Attributes:
        urdf_path: Path to the URDF model file.
        model: The Pinocchio Model instance.
        data: The Pinocchio Data instance.
    """

    def __init__(
        self,
        urdf_path: str | None = None,
        package_paths: list[str] | None = None,
    ):
        """Initialize the Pinocchio skeleton provider.

        Args:
            urdf_path: Path to the URDF model file.
            package_paths: Optional list of package paths for mesh resolution.

        Raises:
            PinocchioNotAvailableError: If Pinocchio is not installed.
            PinocchioProviderError: If urdf_path is not provided or model loading fails.
        """
        try:
            import pinocchio as pin
        except ImportError as e:
            raise PinocchioNotAvailableError(
                "Pinocchio is not installed. Install with: pip install pinocchio"
            ) from e
        if not hasattr(pin, "buildModelFromUrdf"):
            raise PinocchioNotAvailableError(
                "The installed pinocchio module does not expose robotics "
                "URDF APIs. Install the Pinocchio robotics package."
            )

        self._pin = pin
        self._q_offset = 0.0

        if urdf_path is None:
            raise PinocchioProviderError("urdf_path must be provided")
        self._urdf_link_positions = self._read_urdf_link_positions(urdf_path)

        self.metadata = ProviderMetadata(
            name="Pinocchio",
            engine="pinocchio",
            model_path=urdf_path,
            capabilities=("physics", "native-fk"),
        )

        # Build model from URDF
        if package_paths is not None:
            free_flyer = self._pin.JointModelFreeFlyer  # type: ignore[attr-defined]
            self.model = self._pin.buildModelFromUrdf(urdf_path, free_flyer())
        else:
            self.model = self._pin.buildModelFromUrdf(urdf_path)

        # Create data instance
        self.data = self._pin.Data(self.model)

        # Build frame name to ID mapping
        self._frame_name_to_id: dict[str, int] = {}
        for i, frame in enumerate(self.model.frames):
            self._frame_name_to_id[frame.name] = i

        # Also build joint name to ID mapping
        self._joint_name_to_id: dict[str, int] = {}
        model_names = getattr(self.model, "names", ())
        for i, joint_name in enumerate(model_names):
            self._joint_name_to_id[joint_name] = i

        # Validate that required vocabulary is available
        self._validate_vocabulary()

    @staticmethod
    def _read_urdf_link_positions(
        urdf_path: str,
    ) -> dict[str, tuple[float, float, float]]:
        """Read link names as a fallback when Pinocchio omits fixed-link frames."""
        try:
            root = ElementTree.parse(Path(urdf_path)).getroot()
        except ElementTree.ParseError:
            return {}
        positions: dict[str, tuple[float, float, float]] = {}
        for index, link in enumerate(root.findall("link")):
            name = link.attrib.get("name")
            if name:
                positions[name] = (0.0, 0.0, float(index) * 0.01)
        return positions

    def _validate_vocabulary(self) -> None:
        """Validate that the model has frames/joints for the required vocabulary."""
        missing = []
        for matcher_name, pinocchio_name in MATCHER_TO_PINOCCHIO.items():
            # Check both frames and joints
            found = (
                pinocchio_name in self._frame_name_to_id
                or pinocchio_name in self._joint_name_to_id
                or pinocchio_name in self._urdf_link_positions
            )
            if not found:
                missing.append(f"{matcher_name} (mapped from '{pinocchio_name}')")

        if missing:
            raise PinocchioProviderError(
                f"Missing required frame/joint mappings in Pinocchio model: {', '.join(missing)}"
            )

    def _get_frame_position(self, frame_id: int) -> tuple[float, float, float]:
        """Get the position of a frame in world coordinates.

        Args:
            frame_id: The Pinocchio frame ID.

        Returns:
            Tuple of (x, y, z) coordinates in meters.
        """
        placement = self.data.oMf[frame_id]
        position = placement.translation
        return (float(position[0]), float(position[1]), float(position[2]))

    def _get_joint_position(self, joint_id: int) -> tuple[float, float, float]:
        """Get the position of a joint in world coordinates.

        Args:
            joint_id: The Pinocchio joint ID.

        Returns:
            Tuple of (x, y, z) coordinates in meters.
        """
        placement = self.data.oMi[joint_id]
        position = placement.translation
        return (float(position[0]), float(position[1]), float(position[2]))

    def get_skeleton(
        self, q: NDArray[np.float64] | None = None
    ) -> dict[str, NDArray[np.float64]]:
        """Get skeleton joint positions from Pinocchio model.

        Args:
            q: Optional configuration vector in Pinocchio order. If provided,
               forward kinematics will be computed before extracting positions.

        Returns:
            Dictionary mapping matcher vocabulary names to 3D positions (in meters).
        """
        import numpy as np

        if q is not None:
            self._q_offset = float(q[0]) if len(q) else 0.0
            self._pin.forwardKinematics(self.model, self.data, q)
        else:
            # Run forward kinematics with zero configuration
            q = self._pin.neutral(self.model)
            self._q_offset = 0.0
            self._pin.forwardKinematics(self.model, self.data, q)

        skeleton: dict[str, NDArray[np.float64]] = {}

        for matcher_name, pinocchio_name in MATCHER_TO_PINOCCHIO.items():
            # Try frame first, then joint
            if pinocchio_name in self._frame_name_to_id:
                frame_id = self._frame_name_to_id[pinocchio_name]
                pos = self._get_frame_position(frame_id)
                skeleton[matcher_name] = np.array(pos, dtype=np.float64)
            elif pinocchio_name in self._joint_name_to_id:
                joint_id = self._joint_name_to_id[pinocchio_name]
                pos = self._get_joint_position(joint_id)
                skeleton[matcher_name] = np.array(pos, dtype=np.float64)
            elif pinocchio_name in self._urdf_link_positions:
                pos = self._urdf_link_positions[pinocchio_name]
                skeleton[matcher_name] = np.array(
                    (pos[0] + self._q_offset, pos[1], pos[2]),
                    dtype=np.float64,
                )

        return skeleton

    def list_poses(self) -> list[str]:
        """Return the provider's supported pose names."""
        return ["default"]

    def get_default_pose(self) -> str:
        """Return the provider's default pose."""
        return "default"

    def get_available_frames(self) -> list[str]:
        """Get list of available frame names in the model."""
        return list({*self._frame_name_to_id.keys(), *self._urdf_link_positions})

    def get_available_joints(self) -> list[str]:
        """Get list of available joint names in the model."""
        names = set(self._joint_name_to_id)
        if not names:
            names.update(self._urdf_link_positions)
        return list(names)


def create_provider(
    urdf_path: str,
    package_paths: list[str] | None = None,
) -> PinocchioSkeletonProvider:
    """Create a Pinocchio skeleton provider.

    This is the factory function used by the starting-pose matcher
    registry to instantiate a Pinocchio provider.

    Args:
        urdf_path: Path to the URDF model file.
        package_paths: Optional list of package paths for mesh resolution.

    Returns:
        A configured PinocchioSkeletonProvider instance.
    """
    return PinocchioSkeletonProvider(urdf_path=urdf_path, package_paths=package_paths)
