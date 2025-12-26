# engines.physics_engines.drakethon.src.induced_acceleration

Induced Acceleration Analysis for Drake models.

## Classes

### InducedAccelerationResult

Dictionary containing induced acceleration components.

**Inherits from:** typing.TypedDict

### DrakeInducedAccelerationAnalyzer

Analyzes induced accelerations (Gravity, Velocity, Control) for Drake models.

#### Methods

##### compute_components
```python
def compute_components(self: Any, context: Context, tau_app: Any) -> InducedAccelerationResult
```

Compute acceleration components induced by different forces.

Equation: M(q)v_dot + C(q, v)v + G(q) = tau + tau_ext
v_dot = M^-1 * (tau - C - G)

Args:
    context: Drake Context with state (q, v).
    tau_app: Applied control torques (optional).

## Constants

- `M`
