# engines.physics_engines.mujocothon.mujoco_humanoid_golf.joint_analysis

Analysis tools for joint constraint forces, torque transmission, and universal
joints.

This module provides tools for analyzing:
- Constraint forces in universal and gimbal joints
- Torque transmission through multi-DOF joints
- Torque wobble in universal joints (Cardan angles)
- Joint coupling effects

Author: MuJoCo Golf Swing Project

## Classes

### UniversalJointAnalyzer

Analyze universal joint behavior including torque wobble and constraints.

#### Methods

##### get_joint_forces
```python
def get_joint_forces(self: Any, joint_name: str) -> np.ndarray
```

Get constraint forces for a specific joint.

Args:
    joint_name: Name of the joint

Returns:
    Array of constraint forces (size depends on joint DOF)

##### get_universal_joint_angles
```python
def get_universal_joint_angles(self: Any, joint1_name: str, joint2_name: str) -> tuple[Any]
```

Get the two angles of a universal joint (implemented as 2 hinges).

Args:
    joint1_name: Name of first hinge
    joint2_name: Name of second hinge

Returns:
    Tuple of (angle1, angle2) in radians

##### calculate_torque_wobble
```python
def calculate_torque_wobble(self: Any, input_angle: float, joint_angle: float) -> float
```

Calculate torque wobble (variation) due to universal joint geometry.

Universal joints exhibit torque wobble when the two shafts are at an angle.
The output shaft speed varies sinusoidally even if input speed is constant.

Args:
    input_angle: Rotation angle of input shaft (radians)
    joint_angle: Angle between the two shafts (radians)

Returns:
    Angular velocity ratio (output/input)

##### analyze_torque_transmission
```python
def analyze_torque_transmission(self: Any, input_joint: str, output_joint: str, num_cycles: int) -> dict[Any]
```

Analyze torque transmission through a universal joint over full rotations.

Args:
    input_joint: Name of input joint
    output_joint: Name of output joint
    num_cycles: Number of complete rotations to analyze

Returns:
    Dictionary with analysis results

### GimbalJointAnalyzer

Analyze gimbal joint behavior and singularities.

#### Methods

##### get_gimbal_angles
```python
def get_gimbal_angles(self: Any, joint_x: str, joint_y: str, joint_z: str) -> tuple[Any]
```

Get the three Euler angles from a gimbal joint.

Args:
    joint_x: Name of X-axis rotation joint
    joint_y: Name of Y-axis rotation joint
    joint_z: Name of Z-axis rotation joint

Returns:
    Tuple of (angle_x, angle_y, angle_z) in radians

##### check_gimbal_lock
```python
def check_gimbal_lock(self: Any, joint_x: str, joint_y: str, joint_z: str, threshold: float) -> tuple[Any]
```

Check if gimbal is near gimbal lock singularity.

Gimbal lock occurs when the middle ring is rotated ±90 degrees.

Args:
    joint_x: Name of X-axis rotation joint
    joint_y: Name of Y-axis rotation joint (middle ring)
    joint_z: Name of Z-axis rotation joint
    threshold: Threshold in radians for detecting near-gimbal-lock

Returns:
    Tuple of (is_near_lock, distance_to_lock)
