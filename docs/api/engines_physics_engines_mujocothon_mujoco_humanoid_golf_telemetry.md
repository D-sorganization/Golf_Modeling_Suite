# engines.physics_engines.mujocothon.mujoco_humanoid_golf.telemetry

Simulation telemetry utilities for MuJoCo golf swing experiments.

Provides classes to sample joint states, actuator torques, and interaction forces
for every simulation step. Recorded data can be aggregated into summary reports
that describe peak loads and overall simulation coverage, enabling downstream
parameter optimization and comparison of swing configurations.

## Classes

### SimulationSample

Container for per-step telemetry values.

### TelemetryReport

Aggregated view of a simulation run.

#### Methods

##### to_dict
```python
def to_dict(self: Any) -> dict[Any]
```

Convert report to a serializable dictionary.

### TelemetryRecorder

Record telemetry for MuJoCo simulations.

The recorder captures per-step state, actuator torques, and interaction
forces (both joint constraints and external body contacts). Each set of
samples can be converted into a :class:`TelemetryReport` for optimization
pipelines or stored for post-processing.

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Clear captured samples while keeping mappings.

##### add_custom_metric
```python
def add_custom_metric(self: Any, name: str, value: float) -> None
```

Add a custom metric to be recorded in the next step.

Args:
    name: Metric identifier
    value: Scalar value

##### record_step
```python
def record_step(self: Any, data: mujoco.MjData) -> None
```

Capture telemetry for the current simulation state.

##### generate_report
```python
def generate_report(self: Any) -> TelemetryReport
```

Summarize captured telemetry into a report.
