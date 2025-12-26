# engines.physics_engines.mujoco.docker.gui.deepmind_control_suite_MuJoCo_GUI

## Classes

### GolfSimulationGUI

#### Methods

##### load_config
```python
def load_config(self: Any) -> None
```

Load configuration from JSON.

##### save_config
```python
def save_config(self: Any) -> None
```

Save configuration to JSON.

##### setup_styles
```python
def setup_styles(self: Any) -> None
```

Configure modern styling for the application.

##### setup_sim_tab
```python
def setup_sim_tab(self: Any) -> None
```

Setup the simulation tab.

##### setup_appearance_tab
```python
def setup_appearance_tab(self: Any) -> None
```

Setup the appearance tab.

##### setup_equip_tab
```python
def setup_equip_tab(self: Any) -> None
```

Setup the equipment tab.

##### browse_file
```python
def browse_file(self: Any, var: Any, save: Any) -> None
```

Open file dialog to browse for file.

##### update_swatch
```python
def update_swatch(self: Any, part: Any) -> None
```

Update color swatch.

##### pick_color
```python
def pick_color(self: Any, part: Any) -> None
```

Open color picker dialog.

##### log
```python
def log(self: Any, message: Any) -> None
```

Log message to GUI console.

##### clear_log
```python
def clear_log(self: Any) -> None
```

Clear the simulation log.

##### start_simulation
```python
def start_simulation(self: Any) -> None
```

Start the simulation process.

##### stop_simulation
```python
def stop_simulation(self: Any) -> None
```

Stop the simulation process.

##### rebuild_docker
```python
def rebuild_docker(self: Any) -> None
```

Add missing dependencies to the existing robotics_env Docker image.

##### on_sim_success
```python
def on_sim_success(self: Any) -> None
```

Handle successful simulation completion.

##### open_file
```python
def open_file(self: Any, filepath: Any) -> None
```

Open a file with the default application.

##### open_video
```python
def open_video(self: Any) -> None
```

Open the generated video file.

##### open_data
```python
def open_data(self: Any) -> None
```

Open the generated data file.

## Constants

- `DEFAULT_COLORS`
