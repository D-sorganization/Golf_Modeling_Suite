# engines.physics_engines.pinocchiothon.dtack.viz.geppetto_viewer

Geppetto viewer wrapper for desktop visualization.

## Classes

### GeppettoViewer

Geppetto viewer wrapper for Pinocchio models.

Geppetto provides desktop visualization ideal for joint validation.

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
def display(self: Any, q: Any) -> None
```

Display configuration.

Args:
    q: Joint positions [nq]. If None, displays neutral configuration.

## Constants

- `GEPETTO_AVAILABLE`
- `GEPETTO_AVAILABLE`
