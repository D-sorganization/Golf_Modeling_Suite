# sharedthon.engine_manager

Engine Manager for Golf Modeling Suite.

This module provides unified management of different physics engines
including MuJoCo, Drake, Pinocchio, MATLAB models, and pendulum models.

## Classes

### EngineType

Available physics engine types.

**Inherits from:** Enum

### EngineStatus

Engine status types.

**Inherits from:** Enum

### EngineManager

Manages different physics engines for golf swing modeling.

#### Methods

##### get_available_engines
```python
def get_available_engines(self: Any) -> list[EngineType]
```

Get list of available engines.

Returns:
    List of available engine types

##### switch_engine
```python
def switch_engine(self: Any, engine_type: EngineType) -> bool
```

Switch to a different physics engine.

Args:
    engine_type: The engine to switch to

Returns:
    True if switch was successful, False otherwise

##### cleanup
```python
def cleanup(self: Any) -> None
```

Clean up loaded engines.

##### get_current_engine
```python
def get_current_engine(self: Any) -> Any
```

Get the currently active engine.

Returns:
    Current engine type or None if no engine is active

##### get_engine_status
```python
def get_engine_status(self: Any, engine_type: EngineType) -> EngineStatus
```

Get the status of a specific engine.

Args:
    engine_type: The engine to check

Returns:
    Engine status

##### get_engine_info
```python
def get_engine_info(self: Any) -> dict[Any]
```

Get information about all engines.

Returns:
    Dictionary with engine information

##### validate_engine_configuration
```python
def validate_engine_configuration(self: Any, engine_type: EngineType) -> bool
```

Validate that an engine is properly configured.

Args:
    engine_type: The engine to validate

Returns:
    True if engine is properly configured, False otherwise

##### probe_all_engines
```python
def probe_all_engines(self: Any) -> dict[Any]
```

Probe all engines for detailed readiness checks.

Returns:
    Dictionary mapping engine types to probe results

##### get_probe_result
```python
def get_probe_result(self: Any, engine_type: EngineType) -> Any
```

Get probe result for a specific engine.

Args:
    engine_type: The engine to get results for

Returns:
    Probe result or None if not probed

##### get_diagnostic_report
```python
def get_diagnostic_report(self: Any) -> str
```

Get human-readable diagnostic report for all engines.

Returns:
    Formatted diagnostic report

## Constants

- `MUJOCO`
- `DRAKE`
- `PINOCCHIO`
- `MATLAB_2D`
- `MATLAB_3D`
- `PENDULUM`
- `AVAILABLE`
- `UNAVAILABLE`
- `LOADING`
- `LOADED`
- `ERROR`
