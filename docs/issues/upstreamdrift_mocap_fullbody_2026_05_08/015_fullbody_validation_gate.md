# 3D_FullBody_Model: add production validation gate for block budget, signals, and smoke sim

## Context

The Home-license block cap is the controlling constraint for the full-body
Simscape model. Validation must be strong enough that later agents cannot
accidentally add legs/contact/logging that push the model over budget or remove
signals needed by the optimizer.

## Target locations

- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/validate_3d_fullbody.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/tests/test_3d_fullbody_loads.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/docs/`
- CI or local validation scripts if MATLAB is available

## Required behavior

Validation output must include:

- total block count
- nonvirtual block estimate and classification method
- Home-license budget threshold, default 1000
- warning threshold, recommended 900
- signal count and required signal allowlist result
- smoke simulation status and duration
- generated model timestamp/source hash
- whether legs and contact are present

Once the scaffold phase is over, validation should fail if legs/contact are
absent. During scaffold merge, it may warn instead, but that transition must be
explicitly versioned or option-controlled.

## Tests

- Report parser test in Python or MATLAB.
- MATLAB validation test for generated model when present.
- Static script test that validates required fields exist in returned struct.
- Negative test for over-budget report if feasible without Simulink.

## Acceptance criteria

- Full-body PRs include a validation report artifact.
- The report distinguishes scaffold, one-leg, and full-contact phases.
- The model cannot be claimed as complete unless validation says legs/contact
  are present and block budget is below threshold.

## Labels

`enhancement`, `matlab`, `testing`, `quality-control`, `priority:high`
