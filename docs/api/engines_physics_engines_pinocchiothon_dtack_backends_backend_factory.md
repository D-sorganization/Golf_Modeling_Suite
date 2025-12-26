# engines.physics_engines.pinocchiothon.dtack.backends.backend_factory

Factory for creating backend instances.

## Classes

### BackendType

Supported backend types.

**Inherits from:** str, Enum

### BackendFactory

Factory for creating backend instances from canonical model specification.

#### Methods

##### create
```python
def create(backend_type: Any, model_path: Any) -> Any
```

Create a backend instance.

Args:
    backend_type: Type of backend to create
    model_path: Path to canonical model specification or backend-specific file

Returns:
    Backend instance

Raises:
    ValueError: If backend type is not supported

## Constants

- `PINOCCHIO`
- `MUJOCO`
- `PINK`
