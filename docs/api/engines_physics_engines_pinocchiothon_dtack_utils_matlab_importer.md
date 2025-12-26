# engines.physics_engines.pinocchiothon.dtack.utils.matlab_importer

Python utility to import MATLAB data files (.mat, .c3d).

## Classes

### MATLABImporter

Import MATLAB data files for use in Python workflows.

#### Methods

##### load_mat
```python
def load_mat(file_path: Any) -> dict[Any]
```

Load MATLAB .mat file.

Args:
    file_path: Path to .mat file

Returns:
    Dictionary of variable names to arrays

Raises:
    ImportError: If scipy is not installed
    FileNotFoundError: If file does not exist

##### load_c3d
```python
def load_c3d(file_path: Any) -> dict[Any]
```

Load C3D motion capture file.

Args:
    file_path: Path to .c3d file

Returns:
    Dictionary with 'markers', 'analog', 'parameters' keys

Raises:
    ImportError: If ezc3d is not installed
    FileNotFoundError: If file does not exist

##### load_gpcap
```python
def load_gpcap(file_path: Any) -> dict[Any]
```

Load Gears capture file (.gpcap).

Args:
    file_path: Path to .gpcap file

Returns:
    Dictionary with capture data

Raises:
    RuntimeError: Parser not yet implemented. File format requires reverse
        engineering.

## Constants

- `SCIPY_AVAILABLE`
- `EZC3D_AVAILABLE`
- `SCIPY_AVAILABLE`
- `EZC3D_AVAILABLE`
