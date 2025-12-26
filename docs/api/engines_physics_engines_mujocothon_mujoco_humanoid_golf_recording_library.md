# engines.physics_engines.mujocothon.mujoco_humanoid_golf.recording_library

Recording library and database management for golf swing analysis.

Provides:
- SQLite database for metadata
- Recording organization and search
- Tagging and filtering
- Import/export library

## Classes

### RecordingMetadata

Metadata for a golf swing recording.

### RecordingLibrary

Manage a library of golf swing recordings.

#### Methods

##### add_recording
```python
def add_recording(self: Any, data_file: str, metadata: RecordingMetadata, copy_to_library: bool) -> int
```

Add a recording to the library.

Args:
    data_file: Path to recording data file (JSON or CSV)
    metadata: Recording metadata
    copy_to_library: If True, copy file to library directory

Returns:
    Recording ID

Raises:
    FileNotFoundError: If data_file does not exist
    ValueError: If filename is invalid (empty, ".", or "..")
    RuntimeError: If failed to get recording ID from database

##### get_recording
```python
def get_recording(self: Any, recording_id: int) -> Any
```

Get recording metadata by ID.

Args:
    recording_id: Recording ID

Returns:
    RecordingMetadata or None if not found

##### update_recording
```python
def update_recording(self: Any, metadata: RecordingMetadata) -> bool
```

Update recording metadata.

Args:
    metadata: Updated metadata (must have valid ID)

Returns:
    True if successful

##### delete_recording
```python
def delete_recording(self: Any, recording_id: int, delete_file: bool) -> bool
```

Delete a recording.

Args:
    recording_id: Recording ID
    delete_file: If True, also delete the data file (ONLY if within library)

Returns:
    True if successful

##### search_recordings
```python
def search_recordings(self: Any, golfer_name: Any, club_type: Any, swing_type: Any, min_rating: int, tags: Any, date_from: Any, date_to: Any) -> list[RecordingMetadata]
```

Search recordings with filters.

Args:
    golfer_name: Filter by golfer name (partial match)
    club_type: Filter by club type
    swing_type: Filter by swing type
    min_rating: Minimum rating (0-5)
    tags: List of required tags
    date_from: Minimum date (ISO format)
    date_to: Maximum date (ISO format)

Returns:
    List of matching RecordingMetadata

##### get_all_recordings
```python
def get_all_recordings(self: Any) -> list[RecordingMetadata]
```

Get all recordings.

Returns:
    List of all RecordingMetadata

##### get_statistics
```python
def get_statistics(self: Any) -> dict[Any]
```

Get library statistics.

Returns:
    Dictionary with statistics

##### export_library
```python
def export_library(self: Any, output_file: str) -> None
```

Export entire library to JSON.

Args:
    output_file: Output JSON file path

##### import_library
```python
def import_library(self: Any, input_file: str, merge: bool) -> None
```

Import library from JSON.

Args:
    input_file: Input JSON file path
    merge: If True, merge with existing library; if False, replace

##### get_unique_values
```python
def get_unique_values(self: Any, field: str) -> list[str]
```

Get all unique values for a field.

Args:
    field: Field name (e.g., 'golfer_name', 'club_type')

Returns:
    List of unique values

##### get_recording_path
```python
def get_recording_path(self: Any, metadata: RecordingMetadata) -> Path
```

Get full path to recording data file.

Args:
    metadata: Recording metadata

Returns:
    Path to data file
