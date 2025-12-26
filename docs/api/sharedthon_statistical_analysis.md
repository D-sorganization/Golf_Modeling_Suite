# sharedthon.statistical_analysis

Statistical analysis module for golf swing biomechanics.

Provides comprehensive statistical analysis including:
- Peak detection
- Summary statistics
- Swing quality metrics
- Phase-specific analysis

## Classes

### PeakInfo

Information about a detected peak.

### SummaryStatistics

Summary statistics for a time series.

### SwingPhase

Information about a swing phase.

### KinematicSequenceInfo

Information about the kinematic sequence.

### StatisticalAnalyzer

Comprehensive statistical analysis for golf swing data.

#### Methods

##### compute_summary_stats
```python
def compute_summary_stats(self: Any, data: np.ndarray) -> SummaryStatistics
```

Compute summary statistics for a 1D array.

Args:
    data: 1D numpy array

Returns:
    SummaryStatistics object

##### find_peaks_in_data
```python
def find_peaks_in_data(self: Any, data: np.ndarray, height: Any, prominence: Any, distance: Any) -> list[PeakInfo]
```

Find peaks in time series data.

Args:
    data: 1D array
    height: Minimum peak height
    prominence: Minimum peak prominence
    distance: Minimum samples between peaks

Returns:
    List of PeakInfo objects

##### find_club_head_speed_peak
```python
def find_club_head_speed_peak(self: Any) -> Any
```

Find peak club head speed.

Returns:
    PeakInfo for maximum club head speed

##### compute_range_of_motion
```python
def compute_range_of_motion(self: Any, joint_idx: int) -> tuple[Any]
```

Compute range of motion for a joint.

Args:
    joint_idx: Joint index

Returns:
    (min_angle, max_angle, rom) in degrees

##### compute_tempo
```python
def compute_tempo(self: Any) -> Any
```

Compute swing tempo (backswing:downswing ratio).

Uses club head speed to identify transition point.

Returns:
    (backswing_duration, downswing_duration, ratio) or None

##### compute_x_factor
```python
def compute_x_factor(self: Any, shoulder_joint_idx: int, hip_joint_idx: int) -> Any
```

Compute X-Factor (shoulder-hip rotation difference).

Args:
    shoulder_joint_idx: Index of shoulder/torso rotation joint
    hip_joint_idx: Index of hip rotation joint

Returns:
    X-Factor time series (degrees) or None

##### detect_impact_time
```python
def detect_impact_time(self: Any) -> Any
```

Detect ball impact time.

Uses peak club head speed as proxy for impact.

Returns:
    Impact time in seconds, or None

##### compute_energy_metrics
```python
def compute_energy_metrics(self: Any, kinetic_energy: np.ndarray, potential_energy: np.ndarray) -> dict[Any]
```

Compute energy-related metrics.

Args:
    kinetic_energy: Kinetic energy time series
    potential_energy: Potential energy time series

Returns:
    Dictionary of energy metrics

##### detect_swing_phases
```python
def detect_swing_phases(self: Any) -> list[SwingPhase]
```

Automatically detect swing phases.

Uses heuristics based on club head speed and position.

Returns:
    List of SwingPhase objects

##### compute_phase_statistics
```python
def compute_phase_statistics(self: Any, phases: list[SwingPhase], data: np.ndarray) -> dict[Any]
```

Compute statistics for each phase.

Args:
    phases: List of swing phases
    data: 1D data array

Returns:
    Dictionary mapping phase name to statistics

##### generate_comprehensive_report
```python
def generate_comprehensive_report(self: Any) -> dict[Any]
```

Generate comprehensive statistical report.

Returns:
    Dictionary with all analysis results

##### compute_frequency_analysis
```python
def compute_frequency_analysis(self: Any, data: np.ndarray, window: str) -> tuple[Any]
```

Compute frequency analysis (PSD).

Args:
    data: Input time series data
    window: Window function

Returns:
    (frequencies, psd_values)

##### compute_smoothness_metric
```python
def compute_smoothness_metric(self: Any, data: np.ndarray) -> float
```

Compute smoothness metric (Spectral Arc Length).

Args:
    data: Velocity profile (or other signal)

Returns:
    Smoothness score (negative dimensionless value)

##### analyze_kinematic_sequence
```python
def analyze_kinematic_sequence(self: Any, segment_indices: dict[Any]) -> tuple[Any]
```

Analyze the kinematic sequence of the swing.

The kinematic sequence refers to the proximal-to-distal sequencing of
peak rotational velocities (e.g., Pelvis -> Thorax -> Arm -> Club).

Args:
    segment_indices: Dictionary mapping segment names to joint indices.
                     Example: {'Pelvis': 0, 'Thorax': 1, 'Arm': 2}

Returns:
    Tuple of:
    - List of KinematicSequenceInfo objects sorted by peak time
    - Sequence efficiency score (0.0 to 1.0, 1.0 being perfect order)

##### compute_correlations
```python
def compute_correlations(self: Any, data_type: str) -> tuple[Any]
```

Compute correlation matrix for joint data.

Args:
    data_type: Type of data to correlate ('position', 'velocity', 'torque')

Returns:
    Tuple of (correlation_matrix, labels)

##### export_statistics_csv
```python
def export_statistics_csv(self: Any, filename: str, report: Any) -> None
```

Export statistics to CSV file.

Args:
    filename: Output filename
    report: Statistics report (if None, generates new one)
