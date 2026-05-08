# 3D_FullBody_Model: extend polynomial and theta contracts for leg joints

## Context

The full-body design adds hip, knee, and ankle joints. The existing polynomial
contract discovers coefficients by name pattern. The roadmap expects theta to
grow from 189 to 231, but this must be verified in code and tests.

## Target locations

- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/src/model/PolynomialInputValues.mat`
- `src/engines/Simscape_Multibody_Models/3D_Golf_Model/MachineLearning/export_torque_polynomials.py`
- MATLAB helper that implements `getPolynomialParameterInfo()`
- `src/tools/starting_pose_matcher/`
- optimizer and `simulate_with_coefficients` integration tests

## Required behavior

Add or verify coefficient families:

```text
LHipXA..LHipXG, LHipYA..LHipYG, LHipZA..LHipZG
RHipXA..RHipXG, RHipYA..RHipYG, RHipZA..RHipZG
LKneeA..LKneeG, RKneeA..RKneeG
LAnkleXA..LAnkleXG, LAnkleYA..LAnkleYG
RAnkleXA..RAnkleXG, RAnkleYA..RAnkleYG
```

Verify the intended theta dimension:

```text
legacy 3D_Golf_Model: 27 joint families * 7 = 189
3D_FullBody_Model: 33 joint families * 7 = 231
```

If implementation discovers 39 families instead of 33 because each hip/ankle
axis is counted separately, stop and document the true contract before changing
optimizers. The issue must resolve this ambiguity with measured discovery
output from the actual helper.

## Tests

- Unit or MATLAB test for coefficient discovery on full-body MAT file.
- Test that legacy model still discovers the legacy theta dimension.
- Test that full-body model reports its theta dimension explicitly.
- `simulate_with_coefficients` contract tests should distinguish model family
  and expected theta length.

## Acceptance criteria

- The true theta size for full-body is measured and documented.
- Optimizer code fails with clear errors on wrong theta length.
- Legacy model behavior remains unchanged.
- `SPEC.md` records model-family-specific coefficient contract.

## Labels

`enhancement`, `matlab`, `motion`, `parity`, `testing`, `priority:high`
