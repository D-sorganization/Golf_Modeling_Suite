# AffineDrift Integration

This document outlines how we integrate AffineDrift's biomechanical simulation output with the Strokes Gained Optimizer's shot-model dispersion parameters.

## From Drift/Control Decomposition to Dispersion Parameters

The core concept is to map the outputs of the **Drift/Control Decomposition** (Section F of the AffineDrift specification) into the `TiltedBivariateGaussian` parameters used by the `sg-optimizer`.

### The Theory

1. **Drift Component (Passive Dynamics)**: The drift component (Coriolis, gravity, passive constraints) heavily influences the longitudinal (along-target) dispersion. Variations in the passive dynamics across a Monte Carlo simulation of a player's swing lead primarily to inconsistencies in clubhead speed and dynamic loft at impact, manifesting as distance control issues (carry variation).
2. **Control Component (Active Torques)**: The control component (actuation) is tightly coupled with the clubface closure rate. Variations in the active control torques primarily affect the lateral (cross-target) dispersion through face angle and path variations at impact.

### Mapping

We use the variance of these components across a simulated ensemble of swings to modulate a baseline dispersion profile:

```python
sigma_long = base_sigma_long * sqrt(drift_variance)
sigma_lat = base_sigma_lat * sqrt(control_variance)
```

Where `drift_variance` and `control_variance` are normalized metrics derived from the AffineDrift simulation output. The baseline parameters (`base_sigma_long`, `base_sigma_lat`) come from the player's established baseline bag, allowing the simulation to scale dispersion up or down based on the specific swing mechanics being evaluated.

### Future Work

- **Cross-correlation (`rho`)**: Currently, the correlation coefficient `rho` is kept at its baseline value. Future research will explore mapping the cross-covariance between drift and control variations directly to the `rho` parameter.
- **Bias Shift**: Constant biases in the drift/control components could be mapped to directional misses (`bias_long`, `bias_lat`).
