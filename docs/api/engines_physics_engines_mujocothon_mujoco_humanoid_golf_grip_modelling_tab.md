# engines.physics_engines.mujocothon.mujoco_humanoid_golf.grip_modelling_tab

Grip Modelling Tab for Advanced Hand Models.

## Classes

### GripModellingTab

Tab for manipulating advanced hand models (Shadow, Allegro).

**Inherits from:** QtWidgets.QWidget

#### Methods

##### connect_sim_widget
```python
def connect_sim_widget(self: Any, sim_widget: MuJoCoSimWidget) -> None
```

Connect to an external simulation widget.

Args:
   sim_widget: The main simulation widget to connect to.

##### load_current_hand_model
```python
def load_current_hand_model(self: Any) -> None
```

Load the selected hand model with a test cylinder.

##### rebuild_joint_controls
```python
def rebuild_joint_controls(self: Any) -> None
```

Rebuild the joint control widgets for the current model.
