# launchers.golf_launcher

Unified Golf Modeling Suite Launcher (PyQt6)
Features:
- Modern UI with rounded corners.
- Modular Docker Environment Management.
- Integrated Help and Documentation.

## Classes

### DockerCheckThread

**Inherits from:** QThread

#### Methods

##### run
```python
def run(self: Any)
```

Run docker check.

### DockerBuildThread

**Inherits from:** QThread

#### Methods

##### run
```python
def run(self: Any)
```

Run the docker build command.

### EnvironmentDialog

Dialog to manage Docker environment and view dependencies.

**Inherits from:** QDialog

#### Methods

##### setup_ui
```python
def setup_ui(self: Any)
```

Setup the UI components.

##### start_build
```python
def start_build(self: Any)
```

Start the docker build process.

##### append_log
```python
def append_log(self: Any, text: Any)
```

Append text to the log console.

##### build_finished
```python
def build_finished(self: Any, success: Any, msg: Any)
```

Handle build completion.

### HelpDialog

Dialog to display help documentation.

**Inherits from:** QDialog

#### Methods

### GolfLauncher

Main application window for the launcher.

**Inherits from:** QMainWindow

#### Methods

##### init_ui
```python
def init_ui(self: Any)
```

Initialize the user interface.

##### create_model_card
```python
def create_model_card(self: Any, name: Any)
```

Creates a clickable card widget.

##### launch_model_direct
```python
def launch_model_direct(self: Any, name: Any)
```

Selects and immediately launches the model (for double-click).

##### select_model
```python
def select_model(self: Any, name: Any)
```

Select a model and update UI.

##### update_launch_button
```python
def update_launch_button(self: Any)
```

Update the launch button state.

##### apply_styles
```python
def apply_styles(self: Any)
```

Apply custom stylesheets.

##### check_docker
```python
def check_docker(self: Any)
```

Start the docker check thread.

##### on_docker_check_complete
```python
def on_docker_check_complete(self: Any, available: Any)
```

Handle docker check result.

##### open_help
```python
def open_help(self: Any)
```

Open the help dialog.

##### open_environment_manager
```python
def open_environment_manager(self: Any)
```

Open the environment manager dialog.

##### launch_simulation
```python
def launch_simulation(self: Any)
```

Launch the selected simulation.

## Constants

- `REPOS_ROOT`
- `ASSETS_DIR`
- `DOCKER_IMAGE_NAME`
- `GRID_COLUMNS`
- `MODELS_DICT`
- `MODEL_IMAGES`
- `MODEL_DESCRIPTIONS`
- `DOCKER_STAGES`
