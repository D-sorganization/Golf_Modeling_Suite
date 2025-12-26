# sharedthon.physics_parameters

Physics parameter registry for Golf Modeling Suite.

This module provides a central registry for all physics parameters
with validation, units, and source citations.

## Classes

### ParameterCategory

Categories of physics parameters.

**Inherits from:** Enum

### PhysicsParameter

A physics parameter with validation and metadata.

#### Methods

##### validate
```python
def validate(self: Any, new_value: Any) -> tuple[Any]
```

Validate a new value against constraints.

Args:
    new_value: Value to validate

Returns:
    Tuple of (is_valid, error_message)

##### to_dict
```python
def to_dict(self: Any) -> dict[Any]
```

Convert to dictionary for serialization.

### PhysicsParameterRegistry

Central registry for all physics parameters.

#### Methods

##### register
```python
def register(self: Any, param: PhysicsParameter) -> None
```

Register a parameter.

Args:
    param: Parameter to register

##### get
```python
def get(self: Any, name: str) -> Any
```

Get a parameter by name.

Args:
    name: Parameter name

Returns:
    Parameter or None if not found

##### set
```python
def set(self: Any, name: str, value: Any) -> tuple[Any]
```

Set a parameter value with validation.

Args:
    name: Parameter name
    value: New value

Returns:
    Tuple of (success, error_message)

##### get_by_category
```python
def get_by_category(self: Any, category: ParameterCategory) -> list[PhysicsParameter]
```

Get all parameters in a category.

Args:
    category: Parameter category

Returns:
    List of parameters in category

##### get_all_categories
```python
def get_all_categories(self: Any) -> list[ParameterCategory]
```

Get all parameter categories.

Returns:
    List of categories

##### export_to_dict
```python
def export_to_dict(self: Any) -> dict[Any]
```

Export all parameters to dictionary.

Returns:
    Dictionary of parameters

##### export_to_json
```python
def export_to_json(self: Any, filepath: Any) -> None
```

Export parameters to JSON file.

Args:
    filepath: Path to save JSON file

##### import_from_json
```python
def import_from_json(self: Any, filepath: Any) -> int
```

Import parameters from JSON file.

Args:
    filepath: Path to JSON file

Returns:
    Number of parameters imported

##### get_summary
```python
def get_summary(self: Any) -> str
```

Get human-readable summary of all parameters.

Returns:
    Formatted summary

## Constants

- `BALL`
- `CLUB`
- `ENVIRONMENT`
- `BIOMECHANICS`
- `SIMULATION`
