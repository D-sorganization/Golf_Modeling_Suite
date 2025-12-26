# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Motion Capture Plotter.Archive.golf_swing_pyqt6_working

## Classes

### GolfSwingAnalyzerPyQt6

**Inherits from:** QMainWindow

#### Methods

##### setup_ui
```python
def setup_ui(self: Any)
```

Setup the main UI layout

##### create_control_panel
```python
def create_control_panel(self: Any)
```

Create the left control panel

##### create_plot_panel
```python
def create_plot_panel(self: Any)
```

Create the right 3D plot panel

##### setup_3d_scene
```python
def setup_3d_scene(self: Any)
```

Setup the 3D scene with proper coordinate system

##### load_default_data
```python
def load_default_data(self: Any)
```

Try to load the default Excel file

##### load_file
```python
def load_file(self: Any)
```

Load Excel file dialog

##### load_excel_file
```python
def load_excel_file(self: Any, filename: Any)
```

Load and process Excel file with proper coordinate interpretation

##### print_data_debug
```python
def print_data_debug(self: Any, sheet_name: Any)
```

Print debug information about the loaded data

##### update_visualization
```python
def update_visualization(self: Any)
```

Update the 3D visualization with proper coordinate system

##### update_info_display
```python
def update_info_display(self: Any, frame_data: Any)
```

Update the information display

##### on_swing_change
```python
def on_swing_change(self: Any, swing_name: Any)
```

Handle swing selection change

##### on_frame_change
```python
def on_frame_change(self: Any, value: Any)
```

Handle frame slider change

##### on_motion_scale_change
```python
def on_motion_scale_change(self: Any, value: Any)
```

Handle motion scale change

##### on_club_length_change
```python
def on_club_length_change(self: Any, value: Any)
```

Handle club length change

##### update_display_options
```python
def update_display_options(self: Any)
```

Handle display option changes

##### update_frame_info
```python
def update_frame_info(self: Any)
```

Update frame information display

##### toggle_playback
```python
def toggle_playback(self: Any)
```

Toggle play/pause

##### animate
```python
def animate(self: Any)
```

Animation loop for playback - FIXED: Much faster speed

##### set_camera_view
```python
def set_camera_view(self: Any, view: Any)
```

Set predefined camera views

##### reset_view
```python
def reset_view(self: Any)
```

Reset the 3D view

##### on_mouse_press
```python
def on_mouse_press(self: Any, event: Any)
```

Handle mouse button press

##### on_mouse_release
```python
def on_mouse_release(self: Any, event: Any)
```

Handle mouse button release

##### on_mouse_move
```python
def on_mouse_move(self: Any, event: Any)
```

Handle mouse movement

##### on_scroll
```python
def on_scroll(self: Any, event: Any)
```

Handle mouse scroll for zooming - FIXED: Better zoom functionality
