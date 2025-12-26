# Physics Validation Report
==================================================

## MUJOCO Engine

### Conservation Laws
- Energy Conservation: ❌
- Energy Drift: 0.175592
- Momentum Conservation: ✅
- Momentum Drift: 0.000000

### Joint Constraints
- Constraint Satisfaction: ✅
- Max Violation: 0.000000
- Total Violations: 0

### Numerical Stability
- Stable: ✅
- Max Velocity: 5.026
- Max Acceleration: 0.000

## DRAKE Engine

### Conservation Laws
- Energy Conservation: ❌
- Energy Drift: 0.175592
- Momentum Conservation: ✅
- Momentum Drift: 0.000000

### Joint Constraints
- Constraint Satisfaction: ✅
- Max Violation: 0.000000
- Total Violations: 0

### Numerical Stability
- Stable: ✅
- Max Velocity: 5.026
- Max Acceleration: 0.000

## PINOCCHIO Engine

### Conservation Laws
- Energy Conservation: ❌
- Energy Drift: 0.175592
- Momentum Conservation: ✅
- Momentum Drift: 0.000000

### Joint Constraints
- Constraint Satisfaction: ✅
- Max Violation: 0.000000
- Total Violations: 0

### Numerical Stability
- Stable: ✅
- Max Velocity: 5.026
- Max Acceleration: 0.000

## Cross-Engine Comparison

- Engines Compared: mujoco, drake, pinocchio
- Overall Agreement: ✅

### Position Agreement
- mujoco_vs_drake: 0.999
- mujoco_vs_pinocchio: 1.000
- drake_vs_pinocchio: 0.999

### Velocity Agreement
- mujoco_vs_drake: 1.000
- mujoco_vs_pinocchio: 1.000
- drake_vs_pinocchio: 1.000
