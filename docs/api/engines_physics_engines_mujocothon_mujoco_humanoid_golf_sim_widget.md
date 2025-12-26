# engines.physics_engines.mujocothon.mujoco_humanoid_golf.sim_widget

Qt widget encapsulating a MuJoCo simulation and renderer.

## Classes

### MuJoCoSimWidget

Widget that:
- Holds a MuJoCo model + data
- Steps the simulation
- Renders frames with mujoco.Renderer
- Displays frames in a QLabel
- Visualizes forces and torques as 3D vectors
- Records biomechanical data

**Inherits from:** QtWidgets.QWidget

#### Methods

##### load_model_from_xml
```python
def load_model_from_xml(self: Any, xml_string: str) -> None
```

(Re)load a MuJoCo model from an MJCF XML string.

##### load_model_from_file
```python
def load_model_from_file(self: Any, xml_path: str) -> None
```

(Re)load a MuJoCo model from an MJCF XML file path.

Args:
    xml_path: Path to the XML model file (absolute or relative to project root)

Raises:
    FileNotFoundError: If the model file doesn't exist
    ValueError: If the model file is invalid

##### reset_state
```python
def reset_state(self: Any) -> None
```

Set golf-like initial joint angles for all model types.

##### set_operating_mode
```python
def set_operating_mode(self: Any, mode: str) -> None
```

Set the operating mode: 'dynamic' or 'kinematic'.

##### get_dof_info
```python
def get_dof_info(self: Any) -> list[tuple[Any]]
```

Get info for all Degrees of Freedom (joints).

Returns:
    List of (name, (min, max), current_value) tuples.
    Note: This assumes 1-DOF joints (hinge/slide) for simplicity of this UI.
    Complex joints (ball/free) might need special handling.

##### set_joint_qpos
```python
def set_joint_qpos(self: Any, joint_name: str, value: float) -> None
```

Set qpos for a specific 1-DOF joint directly (Kinematic Mode).

##### set_joint_torque
```python
def set_joint_torque(self: Any, index: int, torque: float) -> None
```

Set desired constant torque for actuator index (if it exists).

This is a convenience method that sets constant control.
For advanced control, use get_control_system().

##### get_control_system
```python
def get_control_system(self: Any) -> Any
```

Get the advanced control system.

##### reset_control_system
```python
def reset_control_system(self: Any) -> None
```

Reset the control system (reset time to 0).

##### verify_control_system
```python
def verify_control_system(self: Any) -> bool
```

Verify that control system matches model actuator count.

Returns:
    True if control system is properly initialized and matches model

##### set_running
```python
def set_running(self: Any, running: bool) -> None
```

Set the simulation running state.

##### set_camera
```python
def set_camera(self: Any, camera_name: str) -> None
```

Set the active camera view.

##### set_torque_visualization
```python
def set_torque_visualization(self: Any, enabled: bool, scale: Any) -> None
```

Enable/disable torque vector visualization.

Args:
    enabled: Whether to show torque vectors
    scale: Optional scale factor for arrow length

##### set_force_visualization
```python
def set_force_visualization(self: Any, enabled: bool, scale: Any) -> None
```

Enable/disable force vector visualization.

Args:
    enabled: Whether to show force vectors
    scale: Optional scale factor for arrow length

##### set_ellipsoid_visualization
```python
def set_ellipsoid_visualization(self: Any, mobility_enabled: bool, force_enabled: bool) -> None
```

Enable/disable mobility and force ellipsoid visualization.

##### set_contact_force_visualization
```python
def set_contact_force_visualization(self: Any, enabled: bool) -> None
```

Enable/disable contact force visualization.

##### get_recorder
```python
def get_recorder(self: Any) -> SwingRecorder
```

Get the swing data recorder.

##### get_analyzer
```python
def get_analyzer(self: Any) -> Any
```

Get the biomechanical analyzer.

##### get_jacobian_and_rank
```python
def get_jacobian_and_rank(self: Any) -> dict[Any]
```

Compute Jacobian and Constraint Jacobian Rank.

Returns:
    Dictionary containing:
        - jacobian_condition: condition number of end-effector jacobian
        - constraint_rank: rank of constraint jacobian
        - nefc: number of active constraints

##### compute_ellipsoids
```python
def compute_ellipsoids(self: Any) -> None
```

Compute and draw Mobility and Force Ellipsoids for selected body.

##### render
```python
def render(self: Any) -> None
```

Render the scene immediately.

##### set_background_color
```python
def set_background_color(self: Any, sky_color: Any, ground_color: Any) -> None
```

Set the background colors for the scene.

Args:
    sky_color: RGBA tuple/list for sky color (default: None to keep current)
    ground_color: RGBA tuple/list for ground color (default: None for current)

##### generate_report
```python
def generate_report(self: Any) -> Any
```

Generate a telemetry report for the current simulation.

##### get_manipulator
```python
def get_manipulator(self: Any) -> Any
```

Get the interactive manipulator.

##### mousePressEvent
```python
def mousePressEvent(self: Any, event: QtGui.QMouseEvent) -> None
```

Handle mouse press for body selection and camera control.

##### mouseMoveEvent
```python
def mouseMoveEvent(self: Any, event: Any) -> None
```

Handle mouse move for dragging bodies or camera.

##### mouseReleaseEvent
```python
def mouseReleaseEvent(self: Any, event: Any) -> None
```

Handle mouse release to end dragging.

##### wheelEvent
```python
def wheelEvent(self: Any, event: Any) -> None
```

Handle mouse wheel for camera zoom.

##### set_camera_azimuth
```python
def set_camera_azimuth(self: Any, azimuth: float) -> None
```

Set camera azimuth angle in degrees.

##### set_camera_elevation
```python
def set_camera_elevation(self: Any, elevation: float) -> None
```

Set camera elevation angle in degrees.

##### set_camera_distance
```python
def set_camera_distance(self: Any, distance: float) -> None
```

Set camera distance.

##### set_camera_lookat
```python
def set_camera_lookat(self: Any, x: float, y: float, z: float) -> None
```

Set camera lookat point.

##### reset_camera
```python
def reset_camera(self: Any) -> None
```

Reset camera to default position.

##### show_context_menu
```python
def show_context_menu(self: Any, global_pos: QtCore.QPoint, body_id: int) -> None
```

Show context menu for a body.

##### toggle_frame_visibility
```python
def toggle_frame_visibility(self: Any, body_id: int) -> None
```

Toggle coordinate frame visibility for a body.

##### toggle_com_visibility
```python
def toggle_com_visibility(self: Any, body_id: int) -> None
```

Toggle center of mass visibility for a body.

## Constants

- `LOGGER`
- `J`
- `J`
- `M`
