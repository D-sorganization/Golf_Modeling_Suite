# engines.physics_engines.mujocothon.mujoco_humanoid_golf.urdf_io

URDF import and export functionality for MuJoCo models.

This module provides utilities to convert between MuJoCo MJCF and URDF formats,
enabling model sharing with other robotics frameworks like ROS, Pinocchio, and Drake.

Features:
- Export MuJoCo models to URDF format
- Import URDF models into MuJoCo
- Handle joint type conversions
- Preserve inertial properties
- Convert visual and collision geometries

## Classes

### URDFExporter

Exports MuJoCo models to URDF format.

#### Methods

##### export_to_urdf
```python
def export_to_urdf(self: Any, output_path: Any, model_name: Any) -> str
```

Export MuJoCo model to URDF format.

Args:
    output_path: Path to save URDF file
    model_name: Name for the robot model (defaults to model name)
    include_visual: Include visual geometries
    include_collision: Include collision geometries

Returns:
    URDF XML string

### URDFImporter

Imports URDF models into MuJoCo format.

#### Methods

##### import_from_urdf
```python
def import_from_urdf(self: Any, urdf_path: Any, model_name: Any) -> str
```

Import URDF model and convert to MuJoCo MJCF XML.

Args:
    urdf_path: Path to URDF file
    model_name: Name for the MuJoCo model

Returns:
    MuJoCo MJCF XML string

Note:
    This is a basic implementation. Complex URDF features like
    transmission, gazebo plugins, etc. are not supported.

## Constants

- `MJCF_TO_URDF_JOINT_TYPES`
- `URDF_TO_MJCF_JOINT_TYPES`
