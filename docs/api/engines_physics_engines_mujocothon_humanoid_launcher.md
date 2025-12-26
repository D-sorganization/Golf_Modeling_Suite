# engines.physics_engines.mujocothon.humanoid_launcher

Humanoid Golf Simulation Launcher (PyQt6)
A modern GUI for the MuJoCo Humanoid Golf Model.

## Classes

### SimulationWorker

Worker thread for running Docker simulation to avoid freezing GUI.

**Inherits from:** QThread

#### Methods

##### run
```python
def run(self: Any)
```

### ModernDarkPalette

Custom Dark Palette for a modern look.

**Inherits from:** QPalette

#### Methods

### HumanoidLauncher

**Inherits from:** QMainWindow

#### Methods

##### setup_ui
```python
def setup_ui(self: Any)
```

##### setup_sim_tab
```python
def setup_sim_tab(self: Any)
```

##### enable_results
```python
def enable_results(self: Any, enabled: bool) -> None
```

##### setup_appearance_tab
```python
def setup_appearance_tab(self: Any)
```

##### setup_equip_tab
```python
def setup_equip_tab(self: Any)
```

##### setup_log_area
```python
def setup_log_area(self: Any, parent_layout: Any)
```

##### log
```python
def log(self: Any, msg: Any)
```

##### clear_log
```python
def clear_log(self: Any)
```

##### set_btn_color
```python
def set_btn_color(self: Any, btn: Any, rgba: Any)
```

##### pick_color
```python
def pick_color(self: Any, key: Any, btn: Any)
```

##### on_control_mode_changed
```python
def on_control_mode_changed(self: Any, mode: str) -> None
```

Update the help text and enable/disable polynomial generator button
based on the selected control mode.

##### open_polynomial_generator
```python
def open_polynomial_generator(self: Any)
```

Open polynomial generator dialog.

##### browse_file
```python
def browse_file(self: Any, line_edit: Any, save: Any)
```

##### load_config
```python
def load_config(self: Any)
```

##### save_config
```python
def save_config(self: Any)
```

##### get_docker_cmd
```python
def get_docker_cmd(self: Any)
```

##### plot_induced_acceleration
```python
def plot_induced_acceleration(self: Any)
```

Plot Induced Acceleration Analysis from CSV.

##### start_simulation
```python
def start_simulation(self: Any)
```

##### stop_simulation
```python
def stop_simulation(self: Any)
```

##### on_simulation_finished
```python
def on_simulation_finished(self: Any, code: Any, stderr: Any)
```

##### rebuild_docker
```python
def rebuild_docker(self: Any)
```

##### open_video
```python
def open_video(self: Any)
```

##### open_data
```python
def open_data(self: Any)
```

## Constants

- `DEFAULT_CONFIG`
- `HAS_MATPLOTLIB`
- `HAS_MATPLOTLIB`
