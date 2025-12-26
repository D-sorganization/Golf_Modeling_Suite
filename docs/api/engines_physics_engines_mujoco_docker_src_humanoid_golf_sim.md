# engines.physics_engines.mujoco.docker.src.humanoid_golf.sim

## Classes

### BaseController

#### Methods

##### get_action
```python
def get_action(self: Any, physics: Any) -> np.ndarray
```

Get the control action.

### PDController

**Inherits from:** BaseController

#### Methods

##### get_action
```python
def get_action(self: Any, physics: Any) -> np.ndarray
```

Calculate PD control action.

### PolynomialController

**Inherits from:** BaseController

#### Methods

##### get_action
```python
def get_action(self: Any, physics: Any) -> np.ndarray
```

Calculate polynomial control action.

### LQRController

**Inherits from:** BaseController

#### Methods

##### get_action
```python
def get_action(self: Any, physics: Any) -> np.ndarray
```

Calculate LQR control action.

### TimeStep

Mock dm_env.TimeStep for viewer compatibility.

#### Methods

##### first
```python
def first(self: Any) -> bool
```

##### mid
```python
def mid(self: Any) -> bool
```

##### last
```python
def last(self: Any) -> bool
```

### PhysicsEnvWrapper

Wraps a pure Physics object to satisfy dm_control.viewer's Environment.

#### Methods

##### physics
```python
def physics(self: Any) -> typing.Any
```

Return the physics object.

##### action_spec
```python
def action_spec(self: Any) -> typing.Any
```

Return the action specification.

##### step
```python
def step(self: Any, action: Any) -> TimeStep
```

Advance the environment by one step.

##### reset
```python
def reset(self: Any) -> TimeStep
```

Reset the environment.

### Spec

#### Methods

## Constants

- `TARGET_POSE`
- `HAS_VIEWER`
- `HAS_VIEWER`
- `K`
