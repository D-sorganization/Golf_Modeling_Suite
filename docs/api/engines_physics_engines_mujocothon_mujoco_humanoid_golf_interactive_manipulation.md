# engines.physics_engines.mujocothon.mujoco_humanoid_golf.interactive_manipulation

Interactive drag-and-pose manipulation system for MuJoCo models.

This module provides:
- Mouse picking via ray-casting
- IK-based drag manipulation
- Body constraints (fixed in space or relative to other bodies)
- Pose library (save/load/interpolate poses)
- Visual feedback for selected bodies and constraints

## Classes

### ConstraintType

Types of constraints for fixing segments.

**Inherits from:** Enum

### BodyConstraint

Constraint for fixing a body segment.

### StoredPose

Stored pose configuration.

### MousePickingRay

Ray-casting for mouse picking in 3D scene.

#### Methods

##### screen_to_ray
```python
def screen_to_ray(self: Any, x: int, y: int, width: int, height: int, camera: mujoco.MjvCamera) -> tuple[Any]
```

Convert screen coordinates to 3D ray.

Args:
    x: Screen x coordinate
    y: Screen y coordinate
    width: Viewport width
    height: Viewport height
    camera: MuJoCo camera

Returns:
    Tuple of (ray_origin [3], ray_direction [3])

##### pick_body
```python
def pick_body(self: Any, x: int, y: int, width: int, height: int, camera: mujoco.MjvCamera, max_distance: float) -> Any
```

Pick a body using mouse coordinates.

Args:
    x: Screen x coordinate
    y: Screen y coordinate
    width: Viewport width
    height: Viewport height
    camera: MuJoCo camera
    max_distance: Maximum ray distance

Returns:
    Tuple of (body_id, intersection_point, distance) or None

### InteractiveManipulator

Interactive manipulation system with IK-based dragging and constraints.

#### Methods

##### enable_drag
```python
def enable_drag(self: Any, enabled: bool) -> None
```

Enable or disable drag manipulation.

##### select_body
```python
def select_body(self: Any, x: int, y: int, width: int, height: int, camera: mujoco.MjvCamera) -> Any
```

Select a body at screen coordinates.

Args:
    x: Screen x coordinate
    y: Screen y coordinate
    width: Viewport width
    height: Viewport height
    camera: MuJoCo camera

Returns:
    Selected body ID or None

##### deselect_body
```python
def deselect_body(self: Any) -> None
```

Deselect current body.

##### drag_to
```python
def drag_to(self: Any, x: int, y: int, width: int, height: int, camera: mujoco.MjvCamera, plane_normal: Any) -> bool
```

Drag selected body to screen coordinates using IK.

Args:
    x: Screen x coordinate
    y: Screen y coordinate
    width: Viewport width
    height: Viewport height
    camera: MuJoCo camera
    plane_normal: Normal of drag plane (default: camera view plane)

Returns:
    True if IK succeeded

##### add_constraint
```python
def add_constraint(self: Any, body_id: int, constraint_type: ConstraintType, reference_body_id: Any) -> None
```

Add a constraint to fix a body.

Args:
    body_id: Body to constrain
    constraint_type: Type of constraint
    reference_body_id: Reference body for relative constraints

##### remove_constraint
```python
def remove_constraint(self: Any, body_id: int) -> None
```

Remove constraint from body.

##### toggle_constraint
```python
def toggle_constraint(self: Any, body_id: int) -> bool
```

Toggle constraint active state.

Returns:
    New active state

##### clear_constraints
```python
def clear_constraints(self: Any) -> None
```

Remove all constraints.

##### enforce_constraints
```python
def enforce_constraints(self: Any) -> None
```

Public wrapper to apply all active constraints.

Used by the simulation loop to keep constrained bodies pinned even
when the user is not actively dragging segments.

##### get_constrained_bodies
```python
def get_constrained_bodies(self: Any) -> list[int]
```

Get list of currently constrained bodies.

Returns:
    List of body IDs with active constraints

##### save_pose
```python
def save_pose(self: Any, name: str, description: str) -> StoredPose
```

Save current pose to library.

Args:
    name: Pose name
    description: Optional description

Returns:
    Stored pose

##### load_pose
```python
def load_pose(self: Any, name: str, apply_velocities: bool) -> bool
```

Load pose from library.

Args:
    name: Pose name
    apply_velocities: Whether to apply saved velocities

Returns:
    True if pose was loaded

##### delete_pose
```python
def delete_pose(self: Any, name: str) -> bool
```

Delete pose from library.

Args:
    name: Pose name

Returns:
    True if pose was deleted

##### interpolate_poses
```python
def interpolate_poses(self: Any, pose_name_a: str, pose_name_b: str, alpha: float) -> bool
```

Interpolate between two poses.

Args:
    pose_name_a: First pose name
    pose_name_b: Second pose name
    alpha: Interpolation factor (0.0 = A, 1.0 = B)

Returns:
    True if interpolation succeeded

##### export_pose_library
```python
def export_pose_library(self: Any, filepath: str) -> None
```

Export pose library to JSON file.

Args:
    filepath: Path to save file

##### import_pose_library
```python
def import_pose_library(self: Any, filepath: str) -> int
```

Import pose library from JSON file.

Args:
    filepath: Path to load file

Returns:
    Number of poses imported

##### list_poses
```python
def list_poses(self: Any) -> list[str]
```

Get list of pose names in library.

Returns:
    List of pose names

##### get_body_name
```python
def get_body_name(self: Any, body_id: int) -> str
```

Get name of body.

Args:
    body_id: Body ID

Returns:
    Body name or "body_<id>"

##### find_body_by_name
```python
def find_body_by_name(self: Any, name: str) -> Any
```

Find body ID by name (case-insensitive, partial match).

Args:
    name: Body name pattern

Returns:
    Body ID or None

##### reset_to_original_pose
```python
def reset_to_original_pose(self: Any) -> None
```

Reset to original pose before dragging.

## Constants

- `NONE`
- `FIXED_IN_SPACE`
- `RELATIVE_TO_BODY`
- `J`
