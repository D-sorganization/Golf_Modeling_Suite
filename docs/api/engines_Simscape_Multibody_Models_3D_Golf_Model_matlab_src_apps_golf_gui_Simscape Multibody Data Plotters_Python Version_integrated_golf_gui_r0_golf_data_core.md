# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Simscape Multibody Data Plotters.Python Version.integrated_golf_gui_r0.golf_data_core

Golf Swing Visualizer - Core Data Structures and Processing
High-performance data handling with optimized MATLAB loading and frame processing

## Classes

### FrameData

Optimized frame data structure with validation

#### Methods

##### is_valid
```python
def is_valid(self: Any) -> bool
```

Check if frame data is valid (no NaN/Inf in critical points)

##### shaft_direction
```python
def shaft_direction(self: Any) -> np.ndarray
```

Get normalized shaft direction vector

### RenderConfig

Complete rendering configuration with performance optimizations

### PerformanceStats

Performance monitoring structure

#### Methods

##### update_frame_time
```python
def update_frame_time(self: Any, frame_time: float)
```

Update frame timing statistics

### MatlabDataLoader

High-performance MATLAB data loader with caching and validation

#### Methods

##### load_datasets
```python
def load_datasets(self: Any, baseq_file: str, ztcfq_file: str, delta_file: str) -> tuple[Any]
```

Load all three MATLAB datasets with comprehensive error handling

### FrameProcessor

Process and prepare raw data frames for rendering

#### Methods

##### set_filter
```python
def set_filter(self: Any, filter_type: str)
```

Set the data filter and invalidate dynamics cache.

##### invalidate_cache
```python
def invalidate_cache(self: Any)
```

Invalidate cached dynamics data.

##### get_frame_data
```python
def get_frame_data(self: Any, frame_idx: int) -> FrameData
```

Get processed frame data, including calculated dynamics.

##### get_column_data
```python
def get_column_data(self: Any, df: pd.DataFrame, col_name: str, row_idx: int) -> np.ndarray
```

Extract column data as numpy array with error handling.

##### get_num_frames
```python
def get_num_frames(self: Any) -> int
```

Get total number of frames.

##### get_time_vector
```python
def get_time_vector(self: Any) -> np.ndarray
```

Get time vector.

##### set_filter_type
```python
def set_filter_type(self: Any, filter_type: str)
```

Set the current filter type and invalidate cached filtered data

##### set_filter_param
```python
def set_filter_param(self: Any, param_name: str, value: Any)
```

Set a filter parameter and invalidate cached filtered data

##### set_vector_visibility
```python
def set_vector_visibility(self: Any, vector_type: str, visible: bool)
```

Set visibility for calculated vector types

##### set_vector_scale
```python
def set_vector_scale(self: Any, vector_type: str, scale: float)
```

Set scale for vector rendering

### GeometryUtils

High-performance geometry calculations for 3D visualization

#### Methods

##### rotation_matrix_from_vectors
```python
def rotation_matrix_from_vectors(vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray
```

Create rotation matrix to rotate vec1 to vec2 using Rodrigues formula

##### create_cylinder_mesh
```python
def create_cylinder_mesh(radius: float, height: float, segments: int) -> tuple[Any]
```

Create optimized cylinder mesh with normals

##### create_sphere_mesh
```python
def create_sphere_mesh(radius: float, lat_segments: int, lon_segments: int) -> tuple[Any]
```

Create optimized sphere mesh using UV sphere method

##### create_arrow_mesh
```python
def create_arrow_mesh(shaft_radius: float, shaft_length: float, head_radius: float, head_length: float, segments: int) -> tuple[Any]
```

Create arrow mesh for force/torque visualization

## Constants

- `R`
