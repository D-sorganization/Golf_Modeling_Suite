# engines.physics_engines.mujocothon.mujoco_humanoid_golf.polynomial_generator

Polynomial Function Generator Module.

This module provides a visual interface for generating 6th-order polynomial functions
for joint control. It allows users to:
- Draw trends manually
- Add control points
- Input equations
- Drag/manipulate curves
- Fit polynomials to the visual data

## Classes

### MplCanvas

Matplotlib canvas for PyQt6.

**Inherits from:** FigureCanvasQTAgg

#### Methods

### PolynomialGeneratorWidget

Widget for visually generating polynomial functions.

**Inherits from:** QtWidgets.QWidget

#### Methods

##### set_joints
```python
def set_joints(self: Any, joints: list[str]) -> None
```

Set the list of available joints.
