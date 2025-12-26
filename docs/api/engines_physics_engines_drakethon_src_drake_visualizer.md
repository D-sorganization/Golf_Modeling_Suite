# engines.physics_engines.drakethon.src.drake_visualizer

Drake Meshcat Visualization Helper.

## Classes

### DrakeVisualizer

Helper class to manage advanced visualizations in Meshcat.

#### Methods

##### toggle_frame
```python
def toggle_frame(self: Any, body_name: str, visible: bool) -> None
```

Toggle coordinate frame visualization for a body.

##### update_frame_transforms
```python
def update_frame_transforms(self: Any, context: Context) -> None
```

Update transforms of visible frames.

##### toggle_com
```python
def toggle_com(self: Any, body_name: str, visible: bool) -> None
```

Toggle Center of Mass visualization for a body.

##### update_com_transforms
```python
def update_com_transforms(self: Any, context: Context) -> None
```

Update transforms of visible COMs.

##### draw_ellipsoid
```python
def draw_ellipsoid(self: Any, name: str, rotation_matrix: np.ndarray, radii: np.ndarray, position: np.ndarray, color: tuple[Any]) -> None
```

Draw ellipsoid in Meshcat.

Args:
    name: Unique identifier.
    rotation_matrix: 3x3 rotation (axes).
    radii: Length of semi-axes.
    position: Center position.
    color: (r, g, b, alpha)

##### clear_ellipsoids
```python
def clear_ellipsoids(self: Any) -> None
```

##### clear_all
```python
def clear_all(self: Any) -> None
```

Clear all overlays.

## Constants

- `T`
- `X_WB`
- `X_WB`
- `M_B`
