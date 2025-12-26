# engines.physics_engines.mujocothon.mujoco_humanoid_golf.meshcat_adapter

## Classes

### MuJoCoMeshcatAdapter

Adapts MuJoCo model/data to Meshcat for web-based visualization.

#### Methods

##### open_browser
```python
def open_browser(self: Any)
```

##### load_model_geometry
```python
def load_model_geometry(self: Any)
```

Parses MuJoCo model geoms and creates corresponding Meshcat objects.

##### update
```python
def update(self: Any, data: mujoco.MjData)
```

Updates geometry transforms from MuJoCo data.

##### draw_vectors
```python
def draw_vectors(self: Any, data: mujoco.MjData, show_force: bool, show_torque: bool, force_scale: float, torque_scale: float)
```

Draws force/torque vectors at joints.

##### draw_ellipsoid
```python
def draw_ellipsoid(self: Any, name: str, position: np.ndarray, rotation: np.ndarray, radii: np.ndarray, color: int, opacity: float)
```

Draws an ellipsoid at the specified position/orientation.

Args:
    name: Unique name for the ellipsoid
    position: 3D position vector
    rotation: 3x3 rotation matrix (axes of ellipsoid)
    radii: Length of principal axes (x, y, z)
    color: Hex color
    opacity: Opacity (0-1)

##### clear_ellipsoids
```python
def clear_ellipsoids(self: Any)
```

Clears all drawn ellipsoids.

## Constants

- `T`
- `T`
