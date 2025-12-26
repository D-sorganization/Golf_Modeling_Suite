# launchers.unified_launcher

Unified launcher interface wrapping PyQt GolfLauncher.

This module provides a consistent interface for launch_golf_suite.py
that wraps the PyQt-based GolfLauncher implementation.

## Classes

### UnifiedLauncher

Unified launcher interface compatible with launch_golf_suite.py.

This class wraps the PyQt GolfLauncher to provide a consistent
interface with a mainloop() method as expected by the CLI launcher.

#### Methods

##### mainloop
```python
def mainloop(self: Any) -> int
```

Start the launcher main loop.

Returns:
    Exit code from the application

##### show_status
```python
def show_status(self: Any) -> None
```

Display suite status information.

Shows available engines, their status, and configuration.

##### get_version
```python
def get_version(self: Any) -> str
```

Get suite version from package metadata.

Returns:
    Version string (e.g., "1.0.0-beta")

Note:
    Primary source: Package metadata (installed package)
    Fallback: shared.__version__ (development mode)
    Last resort: Hardcoded default

## Constants

- `PYQT_AVAILABLE`
- `PYQT_AVAILABLE`
