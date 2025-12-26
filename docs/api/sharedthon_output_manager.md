# sharedthon.output_manager

Output Manager for Golf Modeling Suite

Handles all output operations including saving simulation results,
managing file organization, and exporting analysis reports.

## Classes

### OutputFormat

Supported output formats.

**Inherits from:** Enum

### OutputManager

Manages all output operations for the Golf Modeling Suite.

Provides unified interface for saving simulation results, analysis data,
and generating reports across all physics engines.

#### Methods

##### create_output_structure
```python
def create_output_structure(self: Any) -> None
```

Create the standard output directory structure.

##### save_simulation_results
```python
def save_simulation_results(self: Any, results: Any, filename: str, format_type: OutputFormat, engine: str, metadata: Any) -> Path
```

Save simulation results to file.

Args:
    results: Simulation results data
    filename: Output filename (without extension)
    format_type: Output format
    engine: Physics engine name
    metadata: Additional metadata to include

Returns:
    Path to saved file

##### load_simulation_results
```python
def load_simulation_results(self: Any, filename: str, format_type: OutputFormat, engine: str) -> Any
```

Load simulation results from file.

Args:
    filename: Input filename
    format_type: File format
    engine: Physics engine name

Returns:
    Loaded simulation results

##### get_simulation_list
```python
def get_simulation_list(self: Any, engine: Any) -> list[str]
```

Get list of available simulation files.

Args:
    engine: Filter by specific engine (optional)

Returns:
    List of simulation filenames

##### export_analysis_report
```python
def export_analysis_report(self: Any, analysis_data: dict[Any], report_name: str, format_type: str) -> Path
```

Export analysis report.

Args:
    analysis_data: Analysis results and metadata
    report_name: Report filename (without extension)
    format_type: Report format (json, html, pdf)

Returns:
    Path to exported report

##### cleanup_old_files
```python
def cleanup_old_files(self: Any, max_age_days: int) -> int
```

Clean up old files based on age.

Args:
    max_age_days: Maximum age in days before cleanup

Returns:
    Number of files cleaned up

## Constants

- `CSV`
- `JSON`
- `HDF5`
- `PICKLE`
- `PARQUET`
