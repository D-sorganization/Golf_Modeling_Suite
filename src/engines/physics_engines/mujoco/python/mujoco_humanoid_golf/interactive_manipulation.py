=======
# ARCHITECTURE_DEBT:
# This module historically exceeds standard length metrics and accumulates excessive domain responsibility.  # noqa: E501
# It requires domain-aware structural extraction to isolate its internal classes appropriately.  # noqa: E501

"""Interactive drag-and-pose manipulation system for MuJoCo models.

This module provides:
- Mouse picking via ray-casting
- IK-based drag manipulation
- Body constraints (fixed in space or relative to other bodies)
- Pose library (save/load/interpolate poses)
- Visual feedback for selected bodies and constraints
"""

>>>>>>> origin/main
from __future__ import annotations

import mujoco
import numpy as np

from ._constraint_manager import BodyConstraint, ConstraintManagerMixin, ConstraintType
from ._ik_solver import IKSolverMixin
from ._mouse_picking import MousePickingRay
from ._pose_library import PoseLibraryMixin, StoredPose

__all__ = [
    "BodyConstraint",
    "ConstraintType",
    "InteractiveManipulator",
    "MousePickingRay",
    "StoredPose",
]


class InteractiveManipulator(IKSolverMixin, ConstraintManagerMixin, PoseLibraryMixin):
    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData) -> None:
<<<<<<< HEAD
        if not (model is not None):
            raise ValueError("model must be provided")
        self.model = model
        self.data = data

=======
    def screen_to_ray(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        camera: mujoco.MjvCamera,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert screen coordinates to 3D ray.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate
            width: Viewport width
            height: Viewport height
            camera: MuJoCo camera

        Returns:
            Tuple of (ray_origin [3], ray_direction [3])
        """
        # Normalize screen coordinates to [-1, 1]
        if x is None:
            raise ValueError("x must be provided")
        x_ndc = (2.0 * x) / width - 1.0
        y_ndc = 1.0 - (2.0 * y) / height  # Flip y

        # Get camera position and orientation
        cam_pos = camera.lookat.copy()
        cam_distance = camera.distance
        cam_azimuth = np.deg2rad(camera.azimuth)
        cam_elevation = np.deg2rad(camera.elevation)

        # Compute camera frame vectors
        # Forward vector (from lookat to camera)
        forward = np.array(
            [
                np.cos(cam_elevation) * np.sin(cam_azimuth),
                np.cos(cam_elevation) * np.cos(cam_azimuth),
                np.sin(cam_elevation),
            ],
        )

        # Camera position
        ray_origin = cam_pos - forward * cam_distance

        # Right and up vectors
        up_world = np.array([0, 0, 1])
        right = np.cross(up_world, forward)
        right = right / (np.linalg.norm(right) + 1e-8)
        up = np.cross(forward, right)

        # Compute ray direction using field of view
        fovy = 45.0  # Default field of view
        aspect = width / height

        # Ray direction in camera space
        ray_dir = forward.copy()
        ray_dir += right * x_ndc * np.tan(np.deg2rad(fovy / 2)) * aspect
        ray_dir += up * y_ndc * np.tan(np.deg2rad(fovy / 2))
        ray_dir = ray_dir / np.linalg.norm(ray_dir)

        return ray_origin, ray_dir

    def pick_body(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        camera: mujoco.MjvCamera,
        max_distance: float = 100.0,
    ) -> tuple[int, np.ndarray, float] | None:
        """Pick a body using mouse coordinates.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate
            width: Viewport width
            height: Viewport height
            camera: MuJoCo camera
            max_distance: Maximum ray distance

        Returns:
            Tuple of (body_id, intersection_point, distance) or None
        """
        if x is None:
            raise ValueError("x must be provided")
        ray_origin, ray_dir = self.screen_to_ray(x, y, width, height, camera)

        # Test ray against all body geometries
        closest_body = None
        closest_distance = max_distance
        closest_point = None

        for body_id in range(1, self.model.nbody):  # Skip world body (0)
            # Get body position
            body_pos = self.data.xpos[body_id].copy()

            # Simple sphere intersection test
            # (More sophisticated methods could use actual geom shapes)
            to_body = body_pos - ray_origin
            proj_length = np.dot(to_body, ray_dir)

            if proj_length < 0:
                continue

            # Closest point on ray to body
            closest_on_ray = ray_origin + ray_dir * proj_length
            distance_to_body = np.linalg.norm(closest_on_ray - body_pos)

            # Use body's bounding sphere (approximate)
            body_radius = 0.1  # Default radius

            # Get geometries for this body
            for geom_id in range(self.model.ngeom):
                if self.model.geom_bodyid[geom_id] == body_id:
                    # Get geom size
                    geom_size = self.model.geom_size[geom_id]
                    body_radius = max(body_radius, geom_size[0])

            # Check if ray intersects bounding sphere
            if distance_to_body < body_radius * 1.5 and proj_length < closest_distance:
                closest_distance = proj_length
                closest_body = body_id
                closest_point = closest_on_ray

        if closest_body is not None and closest_point is not None:
            return closest_body, closest_point, closest_distance

        return None


class InteractiveManipulator:
    """Interactive manipulation system with IK-based dragging and constraints."""

    def __init__(self, model: mujoco.MjModel, data: mujoco.MjData) -> None:
        """Initialize interactive manipulator.

        Args:
            model: MuJoCo model
            data: MuJoCo data
        """
        if model is None:
            raise ValueError("model must be provided")
        self.model = model
        self.data = data

        # Mouse picking
>>>>>>> origin/main
        self.picker = MousePickingRay(model, data)

        self.ik_damping = 0.05
        self.ik_max_iterations = 20
        self.ik_tolerance = 1e-3
        self.ik_step_size = 0.3

        self.selected_body_id: int | None = None
        self.drag_offset: np.ndarray | None = None
        self.original_qpos: np.ndarray | None = None

        self.constraints: dict[int, BodyConstraint] = {}

        self.pose_library: dict[str, StoredPose] = {}

        self.drag_enabled = True
        self.maintain_orientation = False
        self.use_nullspace_posture = True

    def enable_drag(self, enabled: bool) -> None:
        self.drag_enabled = enabled

    def select_body(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        camera: mujoco.MjvCamera,
    ) -> int | None:
<<<<<<< HEAD
        if not (x is not None):
            raise ValueError("x must be provided")
        if not self.drag_enabled:
            return None

        result = self.picker.pick_body(x, y, width, height, camera)

        if result is not None:
            body_id, intersection_point, _ = result

            self.selected_body_id = body_id
            self.original_qpos = self.data.qpos.copy()

            body_pos = self.data.xpos[body_id].copy()
            self.drag_offset = intersection_point - body_pos

            return body_id

        return None

    def deselect_body(self) -> None:
        self.selected_body_id = None
        self.drag_offset = None
        self.original_qpos = None

    def drag_to(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        camera: mujoco.MjvCamera,
        plane_normal: np.ndarray | None = None,
    ) -> bool:
        if not (x is not None):
            raise ValueError("x must be provided")
        if self.selected_body_id is None or not self.drag_enabled:
            return False

        ray_origin, ray_dir = self.picker.screen_to_ray(x, y, width, height, camera)

        if plane_normal is None:
            cam_azimuth = np.deg2rad(camera.azimuth)
            cam_elevation = np.deg2rad(camera.elevation)
            plane_normal = np.array(
                [
                    np.cos(cam_elevation) * np.sin(cam_azimuth),
                    np.cos(cam_elevation) * np.cos(cam_azimuth),
                    np.sin(cam_elevation),
                ],
            )

        body_pos = self.data.xpos[self.selected_body_id].copy()
        plane_point = body_pos

        denom = np.dot(ray_dir, plane_normal)
        if abs(denom) < 1e-6:
            return False

        t = np.dot(plane_point - ray_origin, plane_normal) / denom
        if t < 0:
            return False

        target_point = ray_origin + ray_dir * t

        if self.drag_offset is not None:
            target_point -= self.drag_offset

        mocap_id = self.model.body_mocapid[self.selected_body_id]
        if mocap_id != -1:
            self.data.mocap_pos[mocap_id] = target_point
            mujoco.mj_forward(self.model, self.data)
            return True

        success = self._solve_ik_for_body(
            self.selected_body_id,
            target_point,
            maintain_orientation=self.maintain_orientation,
        )

        if success:
            self._apply_constraints()

        return success

    def get_body_name(self, body_id: int) -> str:
        if not (body_id is not None):
            raise ValueError("body_id must be provided")
        name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
        if name is not None:
            return str(name)
        return f"body_{body_id}"

    def find_body_by_name(self, name: str) -> int | None:
        if not (name is not None):
            raise ValueError("name must be provided")
        for body_id in range(self.model.nbody):
            body_name = self.get_body_name(body_id)
            if name.lower() in body_name.lower():
                return body_id
        return None

    def reset_to_original_pose(self) -> None:
        if self.original_qpos is not None:
            self.data.qpos[:] = self.original_qpos.copy()
            mujoco.mj_forward(self.model, self.data)
