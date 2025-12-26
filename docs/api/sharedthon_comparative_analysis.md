# sharedthon.comparative_analysis

Comparative analysis module for comparing two golf swings.

This module provides tools to align and compare two sets of swing data,
calculating differences in kinematics, kinetics, and timing.

## Classes

### RecorderInterface

Protocol for a recorder that provides time series data.

**Inherits from:** Protocol

#### Methods

##### get_time_series
```python
def get_time_series(self: Any, field_name: str) -> tuple[Any]
```

Extract time series for a specific field.

Args:
    field_name: Name of the field

Returns:
    Tuple of (times, values)

### ComparisonMetric

Result of a metric comparison between two swings.

### AlignedSignals

Container for two signals aligned on a common time base.

### ComparativeSwingAnalyzer

Analyzes and compares two recorded swings.

#### Methods

##### align_signals
```python
def align_signals(self: Any, field_name: str, num_points: int, joint_idx: Any) -> Any
```

Align two signals by normalizing time to 0-100%.

Args:
    field_name: Name of data field (e.g. 'joint_velocities')
    num_points: Number of points for normalized time base
    joint_idx: Index if field is multidimensional

Returns:
    AlignedSignals object or None if data missing

##### compare_scalars
```python
def compare_scalars(self: Any, metric_name: str, val_a: float, val_b: float) -> ComparisonMetric
```

Create comparison metric for two scalar values.

Args:
    metric_name: Name of metric
    val_a: Value from swing A
    val_b: Value from swing B

Returns:
    ComparisonMetric object

##### compare_peak_speeds
```python
def compare_peak_speeds(self: Any) -> Any
```

Compare peak club head speeds.

##### compare_durations
```python
def compare_durations(self: Any) -> Any
```

Compare swing durations.

##### generate_comparison_report
```python
def generate_comparison_report(self: Any) -> dict[Any]
```

Generate a dictionary summary of the comparison.
