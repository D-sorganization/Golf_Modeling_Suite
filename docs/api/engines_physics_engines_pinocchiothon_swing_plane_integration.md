# engines.physics_engines.pinocchiothon.swing_plane_integration

Swing Plane Analysis Integration for Pinocchio Engine.

This module integrates the shared SwingPlaneAnalyzer with Pinocchio-specific
golf swing simulations, providing consistent swing plane analysis across engines.

## Classes

### PinocchioSwingPlaneAnalyzer

Pinocchio-specific swing plane analysis integration.

#### Methods

##### analyze_trajectory
```python
def analyze_trajectory(self: Any, positions: np.ndarray, timestamps: Any) -> SwingPlaneMetrics
```

Analyze swing plane from Pinocchio trajectory data.

Args:
    positions: Club head positions (N, 3) in world coordinates
    timestamps: Optional timestamps for each position

Returns:
    SwingPlaneMetrics with plane analysis results

##### analyze_double_pendulum_swing
```python
def analyze_double_pendulum_swing(self: Any, joint_angles: np.ndarray, link_lengths: tuple[Any], plane_inclination_deg: float) -> SwingPlaneMetrics
```

Analyze swing plane for double pendulum model.

Args:
    joint_angles: Joint angles (N, 2) - [shoulder, wrist]
    link_lengths: (upper_arm_length, forearm_length) in meters
    plane_inclination_deg: Inclination of swing plane from vertical

Returns:
    SwingPlaneMetrics for the pendulum swing

##### get_plane_visualization_data
```python
def get_plane_visualization_data(self: Any, metrics: SwingPlaneMetrics, extent: float) -> dict[Any]
```

Get data for visualizing the swing plane.

Args:
    metrics: Swing plane metrics from analysis
    extent: Size of plane visualization (meters)

Returns:
    Dictionary with plane mesh data for visualization
