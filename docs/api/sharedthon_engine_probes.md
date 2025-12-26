# sharedthon.engine_probes

Engine readiness probe system.

This module provides infrastructure for checking if physics engines
are properly installed and ready to use, with actionable diagnostics.

## Classes

### ProbeStatus

Status of an engine probe.

**Inherits from:** Enum

### EngineProbeResult

Result of an engine readiness probe.

#### Methods

##### is_available
```python
def is_available(self: Any) -> bool
```

Check if engine is available for use.

##### get_fix_instructions
```python
def get_fix_instructions(self: Any) -> str
```

Get instructions for fixing issues.

### EngineProbe

Base class for engine readiness probes.

#### Methods

##### probe
```python
def probe(self: Any) -> EngineProbeResult
```

Check if engine is ready to use.

Returns:
    Probe result with status and diagnostics

### MuJoCoProbe

Probe for MuJoCo physics engine.

**Inherits from:** EngineProbe

#### Methods

##### probe
```python
def probe(self: Any) -> EngineProbeResult
```

Check MuJoCo readiness.

### DrakeProbe

Probe for Drake physics engine.

**Inherits from:** EngineProbe

#### Methods

##### probe
```python
def probe(self: Any) -> EngineProbeResult
```

Check Drake readiness.

### PinocchioProbe

Probe for Pinocchio physics engine.

**Inherits from:** EngineProbe

#### Methods

##### probe
```python
def probe(self: Any) -> EngineProbeResult
```

Check Pinocchio readiness.

### PendulumProbe

Probe for Pendulum models.

**Inherits from:** EngineProbe

#### Methods

##### probe
```python
def probe(self: Any) -> EngineProbeResult
```

Check Pendulum models readiness.

### MatlabProbe

Probe for MATLAB engine.

**Inherits from:** EngineProbe

#### Methods

##### probe
```python
def probe(self: Any) -> EngineProbeResult
```

Check MATLAB readiness.

## Constants

- `AVAILABLE`
- `MISSING_BINARY`
- `MISSING_ASSETS`
- `VERSION_MISMATCH`
- `NOT_INSTALLED`
- `CONFIGURATION_ERROR`
