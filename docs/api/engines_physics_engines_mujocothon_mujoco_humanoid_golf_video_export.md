# engines.physics_engines.mujocothon.mujoco_humanoid_golf.video_export

Video export module for golf swing animations.

This module provides professional video export capabilities:
- Multiple format support (MP4, AVI, GIF)
- Configurable resolution and frame rate
- Optional metric overlays
- Progress tracking

## Classes

### VideoFormat

Supported video formats.

**Inherits from:** Enum

### VideoResolution

Standard video resolutions.

**Inherits from:** Enum

### VideoExporter

Export MuJoCo simulations as video files.

#### Methods

##### start_recording
```python
def start_recording(self: Any, output_path: str, codec: Any) -> bool
```

Start video recording.

Args:
    output_path: Output file path
    codec: Video codec (default: auto-detect from format)

Returns:
    True if recording started successfully

##### add_frame
```python
def add_frame(self: Any, camera_id: Any, overlay_callback: Any) -> None
```

Add a frame to the video.

Args:
    camera_id: Camera ID to render (None = default)
    overlay_callback: Optional function to overlay metrics on frame

##### finish_recording
```python
def finish_recording(self: Any, output_path: Any) -> None
```

Finish video recording and save file.

Args:
    output_path: Output path (required for GIF)

##### export_recording
```python
def export_recording(self: Any, output_path: str, initial_state: np.ndarray, control_function: Callable[Any], duration: float, camera_id: Any, overlay_callback: Any, progress_callback: Any) -> bool
```

Export a complete simulation as video.

Args:
    output_path: Output file path
    initial_state: Initial qpos and qvel
    control_function: Function that returns control given time
    duration: Simulation duration in seconds
    camera_id: Camera ID for rendering
    overlay_callback: Function to overlay metrics (frame, time, data) -> frame
    progress_callback: Function called with (current_frame, total_frames)

Returns:
    True if export successful

## Constants

- `CV2_AVAILABLE`
- `IMAGEIO_AVAILABLE`
- `MP4`
- `AVI`
- `GIF`
- `HD_720`
- `HD_1080`
- `UHD_4K`
- `CUSTOM`
- `CV2_AVAILABLE`
- `IMAGEIO_AVAILABLE`
