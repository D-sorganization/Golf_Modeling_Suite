# engines.physics_engines.drakethon.src.drake_gui_app

Drake Golf GUI Application using PyQt6.

## Classes

### DrakeRecorder

Records simulation data for analysis.

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

##### start
```python
def start(self: Any) -> None
```

##### stop
```python
def stop(self: Any) -> None
```

##### record
```python
def record(self: Any, t: float, q: np.ndarray, v: np.ndarray, club_pos: Any) -> None
```

##### get_time_series
```python
def get_time_series(self: Any, field_name: str) -> tuple[Any]
```

Implement RecorderInterface.

### DrakeSimApp

Main GUI Window for Drake Golf Simulation.

**Inherits from:** QtWidgets.QMainWindow

#### Methods

## Constants

- `LOGGER`
- `HAS_MATPLOTLIB`
- `HAS_MATPLOTLIB`
- `J`
- `M`
- `X_WB`
- `X_WB`
- `X_WB`
