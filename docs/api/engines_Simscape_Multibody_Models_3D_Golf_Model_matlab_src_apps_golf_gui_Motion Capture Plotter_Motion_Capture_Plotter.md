# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Motion Capture Plotter.Motion_Capture_Plotter

## Classes

### MotionCapturePlotter

**Inherits from:** QMainWindow

#### Methods

##### auto_load_excel_file
```python
def auto_load_excel_file(self: Any)
```

Automatically load the Excel file if it exists in the current directory

##### setup_ui
```python
def setup_ui(self: Any)
```

Setup the main UI

##### create_control_panel
```python
def create_control_panel(self: Any)
```

Create the left control panel with scroll area

##### create_plot_panel
```python
def create_plot_panel(self: Any)
```

Create the right plot panel

##### load_file
```python
def load_file(self: Any)
```

Load data file based on current data source

##### on_data_source_changed
```python
def on_data_source_changed(self: Any, source: Any)
```

Handle data source change

##### auto_load_simscape_csv
```python
def auto_load_simscape_csv(self: Any)
```

Automatically load the Simscape CSV file if it exists

##### load_excel_file
```python
def load_excel_file(self: Any, filename: Any)
```

Load and process Excel file

##### load_simscape_csv
```python
def load_simscape_csv(self: Any, filename: Any)
```

Load and process Simscape CSV file

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

##### calculate_ground_level
```python
def calculate_ground_level(self: Any)
```

Set ground level to fixed -2.5 meters

##### adjust_plot_limits_to_ground
```python
def adjust_plot_limits_to_ground(self: Any)
```

Adjust plot limits so ground level is at the bottom

##### update_visualization
```python
def update_visualization(self: Any)
```

Update the 3D visualization with proper coordinate system

##### visualize_motion_capture_data
```python
def visualize_motion_capture_data(self: Any, frame_data: Any, data: Any)
```

Visualize motion capture data (Excel format)

##### visualize_simscape_data
```python
def visualize_simscape_data(self: Any, frame_data: Any, data: Any)
```

Visualize Simscape multibody data (CSV format)

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
