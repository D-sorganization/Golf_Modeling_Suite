# engines.physics_engines.pinocchiothon.double_pendulum_model.ui.double_pendulum_gui

Interactive driven double pendulum GUI with 3D visualization and advanced features.

Features:
- 3D rotation and zoom
- Gravity toggle
- Inclined plane constraint toggle
- Out-of-plane angle for 3D motion
- Immediate position updates on parameter changes
- Data output with configurable granularity
- Organized input categories
- Visual angle reference indicators

## Classes

### UIEntryConfig

### UserInputs

### DoublePendulumApp

#### Methods

##### start
```python
def start(self: Any) -> None
```

Start or resume simulation.

##### pause
```python
def pause(self: Any) -> None
```

Pause simulation.

##### reset
```python
def reset(self: Any) -> None
```

Reset simulation to initial state.

## Constants

- `TIME_STEP`
- `ANGLE_TOLERANCE_DEG`
- `COM_TOLERANCE`
