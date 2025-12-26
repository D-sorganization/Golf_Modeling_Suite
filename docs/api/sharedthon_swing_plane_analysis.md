# sharedthon.swing_plane_analysis

Swing plane analysis module.

Provides analysis of the golf swing plane, including:
- Fitting a plane to the club head trajectory.
- Calculating deviation from the plane.
- Computing plane orientation (steepness/inclination, direction).

## Classes

### SwingPlaneMetrics

Metrics related to the swing plane.

### SwingPlaneAnalyzer

Analyzes the swing plane from 3D trajectory data.

#### Methods

##### fit_plane
```python
def fit_plane(self: Any, points: np.ndarray) -> tuple[Any]
```

Fit a plane to a set of 3D points using SVD.

Args:
    points: Array of points (N, 3)

Returns:
    Tuple of (centroid, normal)

Raises:
    ValueError: If fewer than 3 points are provided.

##### calculate_deviation
```python
def calculate_deviation(self: Any, points: np.ndarray, centroid: np.ndarray, normal: np.ndarray) -> np.ndarray
```

Calculate signed distance of points from the plane.

Args:
    points: (N, 3)
    centroid: (3,)
    normal: (3,)

Returns:
    deviations: (N,) signed distances

##### analyze
```python
def analyze(self: Any, points: np.ndarray) -> SwingPlaneMetrics
```

Perform full swing plane analysis on trajectory.

Args:
    points: (N, 3) club head trajectory (or similar)

Returns:
    SwingPlaneMetrics object
