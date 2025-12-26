# engines.physics_engines.drakethon.src.drake_golf_model

Drake Golf Model URDF Generator and Diagram Builder.

## Classes

### SegmentParams

Parameters for a single body segment.

### GolfModelParams

Parameters for the entire golf swing model.

### GolfURDFGenerator

Generates URDF for the golf swing model from parameters.

#### Methods

##### add_link
```python
def add_link(self: Any, name: str, mass: float, unit_inertia: UnitInertia, visual_shape_tag: Any, visual_params: Any, com_offset: Any) -> ET.Element
```

Add a link to the model.

##### add_joint
```python
def add_joint(self: Any, name: str, joint_type: str, parent: str, child: str, origin_transform: RigidTransform, axis: Any) -> None
```

Add a joint to the model.

##### generate
```python
def generate(self: Any) -> str
```

Generate the URDF string.

## Constants

- `X_WG`
- `X_C_H`
