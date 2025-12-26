# tests.physics_validation.analytical

Analytical solutions for physics validation baselines.

## Classes

### AnalyticalPendulum

Exact solution for a simple pendulum.

#### Methods

##### potential_energy
```python
def potential_energy(self: Any, theta: float) -> float
```

Calculate potential energy relative to bottom position.

PE = m * g * h
h = L * (1 - cos(theta))

##### kinetic_energy
```python
def kinetic_energy(self: Any, omega: float) -> float
```

Calculate kinetic energy.

KE = 0.5 * I * omega^2

##### total_energy
```python
def total_energy(self: Any, theta: float, omega: float) -> float
```

Calculate total mechanical energy.

### AnalyticalBallistic

Exact solution for a ballistic trajectory (no drag).

#### Methods

##### total_energy
```python
def total_energy(self: Any, height: float, velocity: float) -> float
```

Calculate total energy.

E = PE + KE = mgh + 0.5mv^2
