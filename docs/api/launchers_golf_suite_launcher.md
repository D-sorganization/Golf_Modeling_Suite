# launchers.golf_suite_launcher

Unified Golf Suite Launcher (Local Python Version) - Golf Modeling Suite.

Launches the MuJoCo, Drake, and Pinocchio golf model GUIs from a single interface.
This version assumes all dependencies are installed in the local Python environment
or accessible via `sys.executable`.

It does NOT use Docker. For Docker support, use `golf_launcher.py`.

## Classes

### GolfLauncher

#### Methods

##### log_message
```python
def log_message(self: Any, message: str) -> None
```

Add a timestamped message to the log area.

##### clear_log
```python
def clear_log(self: Any) -> None
```

Clear the log text area.

## Constants

- `PYQT_AVAILABLE`
- `PYQT_AVAILABLE`
