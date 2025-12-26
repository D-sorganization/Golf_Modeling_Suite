# engines.physics_engines.mujocothon.mujoco_humanoid_golf.examples_chaotic_pendulum

Example demonstrations for the chaotic driven pendulum model.

This script demonstrates various control scenarios including:
1. Free oscillation with damping
2. Driven oscillation at resonance
3. PID control for stabilization
4. Energy-based swing-up control
5. Chaos exploration with phase portraits

Run this script to see interactive demonstrations of control principles
using the chaotic pendulum model.

## Classes

### ChaoticPendulumController

Base controller class for chaotic pendulum experiments.

**Inherits from:** abc.ABC

#### Methods

##### get_state
```python
def get_state(self: Any) -> tuple[Any]
```

Get current pendulum state.

##### compute_energy
```python
def compute_energy(self: Any) -> float
```

Compute total mechanical energy of pendulum.

For a driven pendulum, the bob's velocity has contributions from both
the base motion and the pendulum's angular motion.

##### control
```python
def control(self: Any, time: float) -> tuple[Any]
```

Calculate control inputs. Should be overridden.

##### apply_control
```python
def apply_control(self: Any, base_force: Any, pendulum_torque: Any) -> None
```

Apply control inputs to the system.

### FreeOscillationDemo

Demonstrate free oscillation with damping.

**Inherits from:** ChaoticPendulumController

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Reset to initial conditions.

##### control
```python
def control(self: Any, time: Any) -> tuple[Any]
```

No active control - free oscillation.

### ResonanceDrivenDemo

Demonstrate resonance with sinusoidal base forcing.

**Inherits from:** ChaoticPendulumController

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Reset to initial conditions.

##### control
```python
def control(self: Any, time: Any) -> tuple[Any]
```

Apply sinusoidal forcing at specified frequency.

### PIDStabilizationDemo

Stabilize pendulum at upright position using PID control.

**Inherits from:** ChaoticPendulumController

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Reset to near-upright position.

##### control
```python
def control(self: Any, time: Any) -> tuple[Any]
```

PID control to stabilize at upright (θ = π).

### SwingUpControlDemo

Energy-based swing-up followed by stabilization.

**Inherits from:** ChaoticPendulumController

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Reset to downward position.

##### control
```python
def control(self: Any, time: Any) -> tuple[Any]
```

Energy-based swing-up with stabilization.

### ChaosExplorationDemo

Explore chaotic dynamics with strong forcing.

**Inherits from:** ChaoticPendulumController

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Reset with specified initial angle.

##### control
```python
def control(self: Any, time: Any) -> tuple[Any]
```

Apply strong forcing to induce chaos.
