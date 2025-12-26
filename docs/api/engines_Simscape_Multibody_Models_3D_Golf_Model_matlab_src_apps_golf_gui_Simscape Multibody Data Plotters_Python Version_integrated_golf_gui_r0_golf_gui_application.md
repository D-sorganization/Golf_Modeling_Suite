# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Simscape Multibody Data Plotters.Python Version.integrated_golf_gui_r0.golf_gui_application

Golf Swing Visualizer - Tabular GUI Application
Supports multiple data sources including motion capture and future Simulink models

## Classes

### SmoothPlaybackController

Smooth playback controller with frame interpolation for 60+ FPS animation

Features:
- VSync-synchronized rendering (60+ FPS)
- Frame interpolation for smooth motion between keyframes
- Variable playback speed
- Scrubbing support

**Inherits from:** QObject

#### Methods

##### load_frame_processor
```python
def load_frame_processor(self: Any, frame_processor: FrameProcessor)
```

Load frame processor with motion data

##### position
```python
def position(self: Any) -> float
```

Current playback position (0.0 to total_frames - 1)

##### position
```python
def position(self: Any, value: float)
```

Set playback position with interpolation

##### play
```python
def play(self: Any)
```

Start smooth playback

##### pause
```python
def pause(self: Any)
```

Pause playback

##### stop
```python
def stop(self: Any)
```

Stop playback and reset to beginning

##### toggle_playback
```python
def toggle_playback(self: Any)
```

Toggle between play and pause

##### seek
```python
def seek(self: Any, position: float)
```

Seek to specific frame position

##### set_playback_speed
```python
def set_playback_speed(self: Any, speed: float)
```

Set playback speed multiplier (0.5 = half speed, 2.0 = double speed)

### MotionCaptureTab

Tab for motion capture data visualization with smooth playback

**Inherits from:** QWidget

#### Methods

### SimulinkModelTab

Tab for Simulink model data visualization (future)

**Inherits from:** QWidget

#### Methods

### ComparisonTab

Tab for comparing motion capture vs Simulink model data

**Inherits from:** QWidget

#### Methods

### GolfVisualizerWidget

OpenGL widget for 3D golf swing visualization

**Inherits from:** QOpenGLWidget

#### Methods

##### initializeGL
```python
def initializeGL(self: Any)
```

Initialize OpenGL context

##### resizeGL
```python
def resizeGL(self: Any, w: int, h: int)
```

Handle OpenGL widget resize

##### paintGL
```python
def paintGL(self: Any)
```

Render the OpenGL scene

##### load_data_from_dataframes
```python
def load_data_from_dataframes(self: Any, dataframes: tuple[Any])
```

Load data from pandas DataFrames

##### update_frame
```python
def update_frame(self: Any, frame_data: FrameData, render_config: RenderConfig)
```

Update the current frame data and render config

##### set_face_on_view
```python
def set_face_on_view(self: Any)
```

Set camera to face-on view (looking at golfer from front)

##### set_down_the_line_view
```python
def set_down_the_line_view(self: Any)
```

Set camera to down-the-line view (90° from face-on)

##### set_behind_view
```python
def set_behind_view(self: Any)
```

Set camera to behind view (180° from face-on)

##### set_above_view
```python
def set_above_view(self: Any)
```

Set camera to overhead view

##### mousePressEvent
```python
def mousePressEvent(self: Any, event: Any)
```

Handle mouse press events

##### mouseReleaseEvent
```python
def mouseReleaseEvent(self: Any, event: Any)
```

Handle mouse release events

##### mouseMoveEvent
```python
def mouseMoveEvent(self: Any, event: Any)
```

Handle mouse move events

##### wheelEvent
```python
def wheelEvent(self: Any, event: Any)
```

Handle mouse wheel events

##### keyPressEvent
```python
def keyPressEvent(self: Any, event: Any)
```

Handle keyboard shortcuts

### GolfVisualizerMainWindow

Main window for the Golf Swing Visualizer with tabular interface

**Inherits from:** QMainWindow

#### Methods
