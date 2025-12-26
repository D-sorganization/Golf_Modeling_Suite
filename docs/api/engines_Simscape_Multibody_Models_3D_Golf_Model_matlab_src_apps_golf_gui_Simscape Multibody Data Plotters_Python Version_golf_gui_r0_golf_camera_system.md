# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Simscape Multibody Data Plotters.Python Version.golf_gui_r0.golf_camera_system

Golf Swing Visualizer - Advanced Camera System
Sophisticated camera controls with smooth animations, presets, and cinematic features

## Classes

### CameraMode

Camera operation modes

**Inherits from:** Enum

### CameraPreset

Predefined camera positions

**Inherits from:** Enum

### CameraState

Complete camera state

### CameraKeyframe

Camera keyframe for cinematic animations

### CameraConstraints

Camera movement constraints

### SmoothAnimator

Smooth interpolation for camera animations

#### Methods

##### ease_in_out_cubic
```python
def ease_in_out_cubic(t: float) -> float
```

Cubic ease-in-out interpolation

##### ease_in_out_quart
```python
def ease_in_out_quart(t: float) -> float
```

Quartic ease-in-out interpolation

##### ease_elastic_out
```python
def ease_elastic_out(t: float) -> float
```

Elastic ease-out for dramatic effects

##### interpolate_vectors
```python
def interpolate_vectors(start: np.ndarray, end: np.ndarray, t: float, easing_func: Any) -> np.ndarray
```

Interpolate between two vectors with optional easing

##### spherical_interpolation
```python
def spherical_interpolation(start_spherical: tuple[Any], end_spherical: tuple[Any], t: float, easing_func: Any) -> tuple[Any]
```

Spherical interpolation for smooth orbit camera movement

### CameraController

Advanced camera controller with multiple modes and smooth animations

**Inherits from:** QObject

#### Methods

##### get_view_matrix
```python
def get_view_matrix(self: Any) -> np.ndarray
```

Get current view matrix

##### get_projection_matrix
```python
def get_projection_matrix(self: Any, aspect_ratio: float) -> np.ndarray
```

Get current projection matrix

##### get_camera_position
```python
def get_camera_position(self: Any) -> np.ndarray
```

Get current camera position in world coordinates

##### handle_mouse_orbit
```python
def handle_mouse_orbit(self: Any, dx: float, dy: float)
```

Handle mouse orbital movement

##### handle_mouse_pan
```python
def handle_mouse_pan(self: Any, dx: float, dy: float)
```

Handle mouse panning movement

##### handle_mouse_zoom
```python
def handle_mouse_zoom(self: Any, delta: float)
```

Handle mouse wheel zoom

##### update_inertia
```python
def update_inertia(self: Any)
```

Update camera movement with inertia

##### set_preset
```python
def set_preset(self: Any, preset: CameraPreset, animate: bool, duration: float)
```

Set camera to predefined preset

##### animate_to_state
```python
def animate_to_state(self: Any, target_state: CameraState, duration: float, easing: Any)
```

Animate camera to target state

##### stop_animation
```python
def stop_animation(self: Any)
```

Stop any ongoing animation

##### add_keyframe
```python
def add_keyframe(self: Any, time: float, state: Any, easing: QEasingCurve.Type)
```

Add a keyframe for cinematic animation

##### clear_keyframes
```python
def clear_keyframes(self: Any)
```

Clear all cinematic keyframes

##### start_cinematic_playback
```python
def start_cinematic_playback(self: Any, duration: Any, loop: bool)
```

Start cinematic camera playback

##### update_cinematic_camera
```python
def update_cinematic_camera(self: Any, time_delta: float)
```

Update camera position during cinematic playback

##### stop_cinematic_playback
```python
def stop_cinematic_playback(self: Any)
```

Stop cinematic camera playback

##### frame_data
```python
def frame_data(self: Any, data_points: list[np.ndarray], margin: float)
```

Automatically frame camera to view all data points

##### follow_point
```python
def follow_point(self: Any, point: np.ndarray, smooth_factor: float)
```

Smoothly follow a moving point

##### look_at_point
```python
def look_at_point(self: Any, point: np.ndarray, animate: bool, duration: float)
```

Look at a specific point

##### set_mode
```python
def set_mode(self: Any, mode: CameraMode)
```

Set camera operation mode

##### reset_to_default
```python
def reset_to_default(self: Any, animate: bool)
```

Reset camera to default position

##### get_state_dict
```python
def get_state_dict(self: Any) -> dict
```

Get camera state as dictionary for saving

##### load_state_dict
```python
def load_state_dict(self: Any, state_dict: dict, animate: bool)
```

Load camera state from dictionary

## Constants

- `ORBIT`
- `FLY`
- `FOLLOW`
- `CINEMATIC`
- `DEFAULT`
- `SIDE_VIEW`
- `TOP_DOWN`
- `FRONT_VIEW`
- `BEHIND_GOLFER`
- `IMPACT_ZONE`
- `FOLLOW_THROUGH`
