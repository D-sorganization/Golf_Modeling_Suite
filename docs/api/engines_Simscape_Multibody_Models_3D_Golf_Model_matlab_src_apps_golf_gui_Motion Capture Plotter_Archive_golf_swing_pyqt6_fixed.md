# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Motion Capture Plotter.Archive.golf_swing_pyqt6_fixed

## Classes

### GolfSwingAnalyzerPyQt6

**Inherits from:** QMainWindow

#### Methods

##### setup_ui
```python
def setup_ui(self: Any)
```

Setup the main UI

##### create_control_panel
```python
def create_control_panel(self: Any)
```

Create the left control panel

##### create_plot_panel
```python
def create_plot_panel(self: Any)
```

Create the right plot panel

##### load_file
```python
def load_file(self: Any)
```

Load Excel file

##### load_excel_file
```python
def load_excel_file(self: Any, filename: Any)
```

Load and process Excel file

##### print_data_debug
```python
def print_data_debug(self: Any, sheet_name: Any)
```

Print debug information about the loaded data

##### setup_frame_slider
```python
def setup_frame_slider(self: Any)
```

Setup the frame slider

##### on_swing_change
```python
def on_swing_change(self: Any, swing_name: Any)
```

Handle swing selection change

##### on_frame_change
```python
def on_frame_change(self: Any, frame: Any)
```

Handle frame slider change

##### on_speed_change
```python
def on_speed_change(self: Any, speed: Any)
```

Handle speed slider change

##### on_scale_change
```python
def on_scale_change(self: Any, scale: Any)
```

Handle motion scale change

##### on_club_length_change
```python
def on_club_length_change(self: Any, length_cm: Any)
```

Handle club length change

##### toggle_playback
```python
def toggle_playback(self: Any)
```

Toggle play/pause

##### next_frame
```python
def next_frame(self: Any)
```

Advance to next frame

##### setup_3d_scene
```python
def setup_3d_scene(self: Any)
```

Setup the 3D scene with ground plane and ball

##### update_visualization
```python
def update_visualization(self: Any)
```

Update the 3D visualization with proper coordinate system

##### update_info_text
```python
def update_info_text(self: Any, frame_data: Any)
```

Update the information text display

##### set_camera_view
```python
def set_camera_view(self: Any, view: Any)
```

Set predefined camera views

##### reset_view
```python
def reset_view(self: Any)
```

Reset the 3D view to the default isometric view and limits

##### on_scroll
```python
def on_scroll(self: Any, event: Any)
```

Handle mouse scroll for zooming

##### on_mouse_press
```python
def on_mouse_press(self: Any, event: Any)
```

Handle mouse button press for rotation/panning

##### on_mouse_release
```python
def on_mouse_release(self: Any, event: Any)
```

Handle mouse button release

##### on_mouse_move
```python
def on_mouse_move(self: Any, event: Any)
```

Handle mouse movement for rotation/panning
