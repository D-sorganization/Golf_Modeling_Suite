# engines.Simscape_Multibody_Models.3D_Golf_Modelthon.src.c3d_reader

Utilities for loading and interpreting C3D motion-capture files.

## Classes

### C3DEvent

A labeled event occurring at a specific time within a capture.

### C3DMetadata

Describes key properties of a C3D motion-capture recording.

#### Methods

##### marker_count
```python
def marker_count(self: Any) -> int
```

Number of tracked markers in the recording.

##### analog_count
```python
def analog_count(self: Any) -> int
```

Number of analog channels in the recording.

##### duration
```python
def duration(self: Any) -> float
```

Capture duration in seconds, or ``0`` if the rate is missing.

### C3DDataReader

Loads marker trajectories and metadata from a C3D file.

#### Methods

##### get_metadata
```python
def get_metadata(self: Any) -> C3DMetadata
```

Return metadata describing marker labels, frame count, rate, and units.

##### points_dataframe
```python
def points_dataframe(self: Any, include_time: bool, markers: Any, residual_nan_threshold: Any, target_units: Any) -> pd.DataFrame
```

Return marker trajectories as a tidy DataFrame.

Args:
    include_time: Whether to include a time column calculated from the frame
        index and the frame rate reported in the C3D header.
    markers: Optional list of marker names to retain. All markers are
        returned when ``None``.
    residual_nan_threshold: If provided, coordinates with residuals above
        the threshold are replaced with ``NaN`` to make downstream QA
        easier in visualization tools.
    target_units: Optional unit string (``"m"`` or ``"mm"``) for the point
        coordinates. A no-op when ``None`` or when the requested units match
        the file's native units.

Returns:
    DataFrame with columns ``frame``, ``marker``, ``x``, ``y``, ``z``,
    ``residual`` (EzC3D stores residuals in the fourth point channel), and
    an optional ``time`` column in seconds.

##### analog_dataframe
```python
def analog_dataframe(self: Any, include_time: bool) -> pd.DataFrame
```

Return analog channels as a tidy DataFrame.

Rows are ordered by sample index and channel name so downstream GUI
components can easily plot synchronized sensor traces.

##### export_points
```python
def export_points(self: Any, output_path: Any) -> Path
```

Export marker trajectories to a tabular file.

Supported formats are CSV, JSON (records orientation), and NPZ. The
format is inferred from the file extension when ``file_format`` is not
provided.

Args:
    output_path: Destination file path.
    include_time: Include a time column in the output.
    markers: Filter for specific markers.
    residual_nan_threshold: Threshold to filter noisy data.
    target_units: Unit conversion (e.g. 'm', 'mm').
    file_format: Explicit format ('csv', 'json', 'npz').
    sanitize: Whether to sanitize CSV output to prevent Excel Formula Injection.
        Defaults to True. Strings starting with =, +, -, @ will be escaped.

##### export_analog
```python
def export_analog(self: Any, output_path: Any) -> Path
```

Export analog channels to a tabular file.

Supports the same formats as :meth:`export_points`. Empty analog data
produces an output file with headers so downstream automation can rely
on the presence of the export artifact.

Args:
    output_path: Destination file path.
    include_time: Include a time column in the output.
    file_format: Explicit format ('csv', 'json', 'npz').
    sanitize: Whether to sanitize CSV output to prevent Excel Formula Injection.
        Defaults to True.
