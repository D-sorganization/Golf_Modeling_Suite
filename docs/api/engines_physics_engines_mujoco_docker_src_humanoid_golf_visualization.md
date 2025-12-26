# engines.physics_engines.mujoco.docker.src.humanoid_golf.visualization

Enhanced visualization module for MuJoCo humanoid golf simulation.

This module provides:
- Force and torque visualization overlays
- Trajectory tracers that persist through simulation
- Real-time data display

## Classes

### TrajectoryTracer

Manages trajectory traces for bodies in the simulation.

#### Methods

##### add_point
```python
def add_point(self: Any, body_name: Any, position: Any)
```

Add a point to a body's trajectory.

Args:
    body_name: Name of the body
    position: 3D position (x, y, z)

##### get_trace
```python
def get_trace(self: Any, body_name: Any)
```

Get trajectory trace for a body.

Args:
    body_name: Name of the body

Returns:
    List of positions or empty list if no trace exists

##### clear
```python
def clear(self: Any, body_name: Any)
```

Clear traces.

Args:
    body_name: Specific body to clear, or None to clear all

### ForceVisualizer

Visualizes forces and torques in the simulation.

#### Methods

##### get_contact_forces
```python
def get_contact_forces(self: Any)
```

Get all contact forces in the simulation.

Returns:
    List of dicts with contact force information

##### get_joint_torques
```python
def get_joint_torques(self: Any)
```

Get joint torques for all actuators.

Returns:
    Dict mapping actuator names to torque values

##### get_center_of_mass
```python
def get_center_of_mass(self: Any)
```

Get center of mass position and velocity.

Returns:
    Dict with COM position and velocity

## Constants

- `FORCE_COLORS`
- `TRACE_COLORS`
