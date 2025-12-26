# engines.Simscape_Multibody_Models.3D_Golf_Model.matlab.src.apps.golf_gui.Simscape Multibody Data Plotters.Python Version.integrated_golf_gui_r0.wiffle_data_loader

Wiffle_ProV1 Data Loader for Golf Swing Visualizer
Handles Excel-based motion capture data and converts to the GUI's expected format

## Classes

### MotionDataConfig

Configuration for motion capture data processing

#### Methods

### MotionDataLoader

Loader for motion capture Excel data

#### Methods

##### load_data
```python
def load_data(self: Any) -> dict[Any]
```

Load Wiffle_ProV1 data from the default Excel file location

Returns:
    Dictionary with 'ProV1' and 'Wiffle' DataFrames

##### load_from_file
```python
def load_from_file(self: Any, filepath: str) -> dict[Any]
```

Load Wiffle_ProV1 Excel data from a specific file path

Args:
    filepath: Path to the Excel file

Returns:
    Dictionary with 'ProV1' and 'Wiffle' DataFrames

##### load_excel_data
```python
def load_excel_data(self: Any, filepath: str) -> dict[Any]
```

Load Wiffle_ProV1 Excel data and convert to GUI-compatible format

Args:
    filepath: Path to the Excel file

Returns:
    Dictionary with 'ProV1' and 'Wiffle' DataFrames

##### convert_to_gui_format
```python
def convert_to_gui_format(self: Any, excel_data: dict[Any]) -> tuple[Any]
```

Convert Excel data to the format expected by the GUI

Args:
    excel_data: Dictionary with 'ProV1' and 'Wiffle' DataFrames

Returns:
    Tuple of (BASEQ, ZTCFQ, DELTAQ) DataFrames for GUI compatibility
