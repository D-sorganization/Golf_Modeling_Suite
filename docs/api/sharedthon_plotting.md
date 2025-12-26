# sharedthon.plotting

Advanced plotting and visualization for golf swing analysis.

This module provides comprehensive plotting capabilities including:
- Time series plots (kinematics, kinetics, energetics)
- Phase diagrams
- Force/torque visualizations
- Power and energy analysis
- Swing sequence analysis

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

### GolfSwingPlotter

Creates advanced plots for golf swing analysis.

This class generates various plots from recorded swing data,
including kinematics, kinetics, energetics, and phase diagrams.
It is engine-agnostic, relying on a generic recorder interface.

#### Methods

##### get_joint_name
```python
def get_joint_name(self: Any, joint_idx: int) -> str
```

Get human-readable joint name.

##### plot_joint_angles
```python
def plot_joint_angles(self: Any, fig: Figure, joint_indices: Any) -> None
```

Plot joint angles over time.

Args:
    fig: Matplotlib figure to plot on
    joint_indices: List of joint indices to plot (None = all)

##### plot_joint_velocities
```python
def plot_joint_velocities(self: Any, fig: Figure, joint_indices: Any) -> None
```

Plot joint velocities over time.

Args:
    fig: Matplotlib figure to plot on
    joint_indices: List of joint indices to plot (None = all)

##### plot_joint_torques
```python
def plot_joint_torques(self: Any, fig: Figure, joint_indices: Any) -> None
```

Plot applied joint torques over time.

Args:
    fig: Matplotlib figure to plot on
    joint_indices: List of joint indices to plot (None = all)

##### plot_actuator_powers
```python
def plot_actuator_powers(self: Any, fig: Figure) -> None
```

Plot actuator mechanical powers over time.

Args:
    fig: Matplotlib figure to plot on

##### plot_energy_analysis
```python
def plot_energy_analysis(self: Any, fig: Figure) -> None
```

Plot kinetic, potential, and total energy over time.

Args:
    fig: Matplotlib figure to plot on

##### plot_club_head_speed
```python
def plot_club_head_speed(self: Any, fig: Figure) -> None
```

Plot club head speed over time.

Args:
    fig: Matplotlib figure to plot on

##### plot_club_head_trajectory
```python
def plot_club_head_trajectory(self: Any, fig: Figure) -> None
```

Plot 3D club head trajectory.

Args:
    fig: Matplotlib figure to plot on

##### plot_phase_diagram
```python
def plot_phase_diagram(self: Any, fig: Figure, joint_idx: int) -> None
```

Plot phase diagram (angle vs angular velocity) for a joint.

Args:
    fig: Matplotlib figure to plot on
    joint_idx: Index of joint to plot

##### plot_torque_comparison
```python
def plot_torque_comparison(self: Any, fig: Figure) -> None
```

Plot comparison of all joint torques (stacked area or grouped bars).

Args:
    fig: Matplotlib figure to plot on

##### plot_frequency_analysis
```python
def plot_frequency_analysis(self: Any, fig: Figure, joint_idx: int, signal_type: str) -> None
```

Plot frequency content (PSD) of a joint signal.

Args:
    fig: Matplotlib figure
    joint_idx: Joint index
    signal_type: 'position', 'velocity', or 'torque'

##### plot_spectrogram
```python
def plot_spectrogram(self: Any, fig: Figure, joint_idx: int, signal_type: str) -> None
```

Plot spectrogram of a joint signal.

Args:
    fig: Matplotlib figure
    joint_idx: Joint index
    signal_type: 'position', 'velocity', or 'torque'

##### plot_summary_dashboard
```python
def plot_summary_dashboard(self: Any, fig: Figure) -> None
```

Create a comprehensive dashboard with multiple subplots.

Args:
    fig: Matplotlib figure to plot on

##### plot_kinematic_sequence
```python
def plot_kinematic_sequence(self: Any, fig: Figure, segment_indices: dict[Any]) -> None
```

Plot kinematic sequence (normalized velocities).

Visualizes proximal-to-distal sequencing.

Args:
    fig: Matplotlib figure
    segment_indices: Map of segment names to joint indices

##### plot_3d_phase_space
```python
def plot_3d_phase_space(self: Any, fig: Figure, joint_idx: int) -> None
```

Plot 3D phase space (Position vs Velocity vs Acceleration).

Args:
    fig: Matplotlib figure
    joint_idx: Joint index

##### plot_correlation_matrix
```python
def plot_correlation_matrix(self: Any, fig: Figure, data_type: str) -> None
```

Plot correlation matrix between joints.

Args:
    fig: Matplotlib figure
    data_type: 'position', 'velocity', or 'torque'

##### plot_swing_plane
```python
def plot_swing_plane(self: Any, fig: Figure) -> None
```

Plot fitted swing plane and trajectory deviation.

Args:
    fig: Matplotlib figure

### MplCanvas

Matplotlib canvas for embedding in PyQt6.

**Inherits from:** FigureCanvasQTAgg

#### Methods

### MplCanvas

Matplotlib canvas for embedding in PyQt6 (not available in headless mode).

#### Methods
