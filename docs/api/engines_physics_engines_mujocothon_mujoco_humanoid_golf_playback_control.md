# engines.physics_engines.mujocothon.mujoco_humanoid_golf.playback_control

Playback control for recorded simulations.

Provides:
- Frame-by-frame stepping
- Variable playback speed
- Timeline scrubbing
- Loop control

## Classes

### PlaybackMode

Playback modes.

**Inherits from:** Enum

### PlaybackController

Control playback of recorded simulation data.

#### Methods

##### play
```python
def play(self: Any) -> None
```

Start playback.

##### pause
```python
def pause(self: Any) -> None
```

Pause playback.

##### stop
```python
def stop(self: Any) -> None
```

Stop playback and reset to start.

##### is_playing
```python
def is_playing(self: Any) -> bool
```

Check if currently playing.

##### step_forward
```python
def step_forward(self: Any, num_frames: int) -> None
```

Step forward by frames.

Args:
    num_frames: Number of frames to step

##### step_backward
```python
def step_backward(self: Any, num_frames: int) -> None
```

Step backward by frames.

Args:
    num_frames: Number of frames to step

##### seek_to_frame
```python
def seek_to_frame(self: Any, frame: int) -> None
```

Seek to specific frame.

Args:
    frame: Frame index (0 to num_frames-1)

##### seek_to_time
```python
def seek_to_time(self: Any, time: float) -> None
```

Seek to specific time.

Args:
    time: Time in seconds

##### seek_to_percent
```python
def seek_to_percent(self: Any, percent: float) -> None
```

Seek to percentage of total duration.

Args:
    percent: Percentage (0.0 to 100.0)

##### set_speed
```python
def set_speed(self: Any, speed: float) -> None
```

Set playback speed.

Args:
    speed: Speed multiplier (0.1 to 10.0)
          1.0 = normal speed
          0.5 = half speed
          2.0 = double speed

##### set_loop
```python
def set_loop(self: Any, loop: bool) -> None
```

Enable/disable looping.

Args:
    loop: Whether to loop playback

##### update
```python
def update(self: Any, dt: float) -> bool
```

Update playback state.

Call this at regular intervals (e.g., 60 Hz).

Args:
    dt: Time step in seconds (real time)

Returns:
    True if frame changed

##### get_current_state
```python
def get_current_state(self: Any) -> tuple
```

Get current state and control.

Returns:
    (state, control, time) tuple

##### get_current_time
```python
def get_current_time(self: Any) -> float
```

Get current playback time.

##### get_current_frame
```python
def get_current_frame(self: Any) -> int
```

Get current frame index.

##### get_progress_percent
```python
def get_progress_percent(self: Any) -> float
```

Get playback progress as percentage.

Returns:
    Progress (0.0 to 100.0)

##### get_info
```python
def get_info(self: Any) -> dict
```

Get playback information.

Returns:
    Dictionary with playback info

##### export_frame_as_image
```python
def export_frame_as_image(self: Any, frame: int, output_path: str, render_callback: Callable[Any]) -> None
```

Export a specific frame as image.

Args:
    frame: Frame index
    output_path: Output image path
    render_callback: Function that takes (state, control) and returns RGB image

### PlaybackSpeedPresets

Common playback speed presets.

#### Methods

##### get_all_presets
```python
def get_all_presets(cls: Any) -> list
```

Get all preset speeds.

## Constants

- `STOPPED`
- `PLAYING`
- `PAUSED`
- `VERY_SLOW`
- `SLOW`
- `HALF`
- `NORMAL`
- `DOUBLE`
- `FAST`
- `VERY_FAST`
