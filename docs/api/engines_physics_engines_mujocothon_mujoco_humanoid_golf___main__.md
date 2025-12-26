# engines.physics_engines.mujocothon.mujoco_humanoid_golf.__main__

Entry point and main window for the MuJoCo golf pendulum demo.

## Classes

### MainWindow

**Inherits from:** QtWidgets.QMainWindow

#### Methods

##### load_current_model
```python
def load_current_model(self: Any) -> None
```

Load selected model and recreate actuator controls.

##### on_model_changed
```python
def on_model_changed(self: Any, index: int) -> None
```

Handle model selection change.

##### on_play_pause_toggled
```python
def on_play_pause_toggled(self: Any, checked: bool) -> None
```

Handle play/pause button toggle.

##### on_reset_clicked
```python
def on_reset_clicked(self: Any) -> None
```

Reset simulation to initial state.

##### on_actuator_changed
```python
def on_actuator_changed(self: Any) -> None
```

Update actuator torques when any slider changes.
