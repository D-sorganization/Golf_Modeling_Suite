# [MEDIUM] Sensor noise models (IMU / force-torque) are toy-grade

## Summary

`src/robotics/sensing/` provides IMU and force-torque sensors that are
Gaussian-noise wrappers. Real sensors have bias drift, misalignment,
scale-factor error, quantization, bandwidth limits, and — critically
for a swing — temperature transients during impact. Sim-to-real
transfer of any controller trained in this simulator will not survive
real hardware.

## Findings

### 1. IMU orientation integration uses first-order angle-axis update

`src/robotics/sensing/imu_sensor.py:240-279`

For `‖ω‖ > 50 rad/s` (easily reached in a driver downswing) the
first-order update has several-degree error per millisecond. Use
the exponential map `q_{n+1} = q_n ⊗ exp(½ω·dt)` with a full
Rodrigues formula, or RK4 on the quaternion.

### 2. No IMU bias drift, temperature, or scale-factor error

`imu_sensor.py` noise is white Gaussian. Real MEMS IMUs have:
- Bias instability (Allan variance plateau) ~ 0.01 °/s/√Hz
- Bias random walk over minutes
- Temperature-dependent bias drift
- Scale-factor error ~0.1 %
- Axis misalignment ~0.1 °
- Quantization to 16-bit or 12-bit

None of these are modeled.

### 3. Force-torque sensor has no temperature drift, no cross-axis coupling

`src/robotics/sensing/force_torque_sensor.py:87-117`

Noise is Brownian + Gaussian. Missing: temperature drift (critical
for club impact which thermally shocks the load cell), cross-axis
coupling (typically 1–3 %), scale factor calibration error.

### 4. Low-frequency sensor artefacts (1/f noise, drift) unmodeled

No pink-noise component, no bias random-walk. Long-horizon experiments
will present IMUs as ideal, which is false.

### 5. Noise generators share global np.random state

`src/robotics/sensing/noise_models.py:62-64, 106-109` — noise
instances with the same seed produce identical sequences. No warning
or check; user can accidentally correlate "independent" noise sources.

### 6. BandwidthLimitedNoise has a minimum-order issue with no guidance

`noise_models.py:195-203` — `order = 0` raises, but order = 1 is
inadequate for typical cutoffs; no doc guides the choice.

### 7. No mocap / marker sensors

Retargeting (`src/learning/retargeting/`) expects marker trajectories,
but there is no `OpticalMarkerSensor` that adds mocap noise, marker
swaps, marker dropouts, and occlusion. Any sim-to-real from retargeted
data assumes ideal mocap.

## Impact

Sim-to-real transfer from this suite will see a 10–100× larger gap
than the current randomization bounds suggest.

## Acceptance Criteria

- [ ] Replace first-order quaternion integration with the exponential
      map; add a test on ω = 80 rad/s.
- [ ] Add `IMUBiasModel` (bias-instability, random-walk, scale factor,
      misalignment, temperature). Parameters taken from a published
      IMU data sheet cited in the docstring.
- [ ] Add temperature-drift and cross-axis coupling to
      `ForceTorqueSensor`. Cite reference hardware (e.g., ATI Nano17).
- [ ] Add `OpticalMarkerSensor` with dropouts, swaps, and occlusion.
- [ ] Seed-collision warning in `NoiseGenerator.__init__`.
- [ ] Parametrize `BandwidthLimitedNoise.order` per-instance and
      document recommended values.

## Related

- Issue #025 — learning subsystem depends on realistic sensors for
  sim-to-real claims.
- Issue #018 — launch-monitor ingestion is the inbound mocap pathway.
