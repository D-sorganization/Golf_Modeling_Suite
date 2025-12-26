# engines.physics_engines.pinocchiothon.double_pendulum_model.physics.triple_pendulum

## Classes

### TripleSegmentProperties

#### Methods

##### center_of_mass_distance
```python
def center_of_mass_distance(self: Any) -> float
```

##### inertia_about_proximal_joint
```python
def inertia_about_proximal_joint(self: Any) -> float
```

### TriplePendulumParameters

#### Methods

##### default
```python
def default(cls: Any) -> TriplePendulumParameters
```

##### gravity
```python
def gravity(self: Any) -> float
```

### TriplePendulumState

### TripleJointTorques

### PolynomialProfile

#### Methods

##### omega
```python
def omega(self: Any, t: float) -> float
```

##### alpha
```python
def alpha(self: Any, t: float) -> float
```

### TriplePendulumDynamics

#### Methods

##### mass_matrix
```python
def mass_matrix(self: Any, state: TriplePendulumState) -> np.ndarray
```

##### bias_vector
```python
def bias_vector(self: Any, state: TriplePendulumState) -> np.ndarray
```

##### forward_dynamics
```python
def forward_dynamics(self: Any, state: TriplePendulumState, control: tuple[Any]) -> tuple[Any]
```

##### inverse_dynamics
```python
def inverse_dynamics(self: Any, state: TriplePendulumState, accelerations: tuple[Any]) -> tuple[Any]
```

##### joint_torque_breakdown
```python
def joint_torque_breakdown(self: Any, state: TriplePendulumState, control: tuple[Any]) -> TripleJointTorques
```

##### step
```python
def step(self: Any, _t: float, state: TriplePendulumState, dt: float, control: tuple[Any]) -> TriplePendulumState
```

## Constants

- `GRAVITATIONAL_ACCELERATION`
- `DAMPING_DEFAULT`
