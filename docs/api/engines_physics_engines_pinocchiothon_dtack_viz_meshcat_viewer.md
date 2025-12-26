# engines.physics_engines.pinocchiothon.dtack.viz.meshcat_viewer

MeshCat viewer wrapper for browser visualization.

## Classes

### MeshCatViewer

MeshCat viewer wrapper for Pinocchio models.

#### Methods

##### load_model
```python
def load_model(self: Any, model: pin.Model, visual_model: Any) -> None
```

Load Pinocchio model into viewer.

Args:
    model: Pinocchio model
    visual_model: Optional visual geometry model

##### display
```python
def display(self: Any, q: npt.NDArray[np.float64]) -> None
```

Display configuration.

Args:
    q: Joint positions [nq]

##### close
```python
def close(self: Any) -> None
```

Close viewer.

## Constants

- `MESHCAT_AVAILABLE`
- `MESHCAT_AVAILABLE`
