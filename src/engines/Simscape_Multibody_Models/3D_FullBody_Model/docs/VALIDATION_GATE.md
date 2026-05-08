# 3D_FullBody_Model Validation Gate

`validate_3d_fullbody.m` is the production gate for the generated
`GolfSwing3D_FullBody.slx` artifact. It exists so later work on legs,
feet, contact forces, and logging cannot silently exceed the Simscape
Home-license block budget or remove signals needed by downstream
optimizers.

## Report Artifact

The build writes `matlab/output/validation_report.json` when
`build_3d_fullbody` runs validation. The report schema is
`3d_fullbody_validation_report.v2` and includes:

- `total_block_count`
- `nonvirtual_block_estimate`
- `nonvirtual_classification_method`
- `home_license_budget`
- `warning_threshold`
- `block_budget`
- `signal_count`
- `required_signal_allowlist`
- `generated_model`
- `source_model_hash_sha256`
- `leg_contact`
- `smoke_sim`
- `failure_messages`
- `warnings`
- `passed`

`generated_model` records whether the generated `.slx` exists, its
timestamp, byte size, and SHA-256 hash. `source_model_hash_sha256`
records the source model hash when a source path is provided.

## Block Budget

The hard budget is the Home-license nonvirtual block cap:

- default budget: `1000`
- warning threshold: `900`

The nonvirtual estimate uses a documented `BlockType` heuristic. Simulink
routing and shell blocks such as `SubSystem`, `Mux`, `Demux`, `Inport`,
`Outport`, `BusCreator`, `BusSelector`, `Goto`, `From`, and trigger/action
ports are treated as virtual. Everything else is counted as nonvirtual.

The gate fails when `nonvirtual_block_estimate > home_license_budget`.
The gate warns when the estimate is above the warning threshold and still
inside the hard budget.

## Signal Allowlist

The report counts unique blocks with `DataLogging` or `LogSimulationData`
enabled plus `Outport` blocks. The default required signal fragments are:

- `CombinedSignalBus`
- `Club`
- `Hip`
- `Torso`
- `Shoulder`
- `Elbow`
- `Wrist`

The `required_signal_allowlist` section reports `required`, `present`,
`missing`, and `passed`. Scaffold mode records missing signals as warnings
unless the caller sets `enforce_required_signals=true`. Production phases
enforce the allowlist by default.

## Phase Ratchet

The same gate supports three phases:

| Phase          | Required behavior                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------------- |
| `scaffold`     | Generated model, block budget, signal inventory, and smoke sim are checked. Missing legs/contact are warnings. |
| `one_leg`      | At least one scripted leg chain must be present. Missing required signals fail by default.                     |
| `full_contact` | Left leg, right leg, and ground contact must be present. Missing required signals fail by default.             |

Use `build_3d_fullbody(struct('validation_phase', 'one_leg'))` once the
one-leg script is stable, and ratchet to
`build_3d_fullbody(struct('validation_phase', 'full_contact'))` only when
both legs and contact force wiring are implemented.

## Smoke Simulation

The smoke simulation uses `Simulink.SimulationInput`, disables Fast
Restart, and runs to `smoke_time` seconds. The default is `0.005` seconds.
Set `smoke_time <= 0` only for static validation. A failed smoke sim always
fails the gate; warning stop events are recorded in `warnings`.

## Local Commands

From `3D_FullBody_Model/matlab/scripts`:

```matlab
build_3d_fullbody
```

Static or focused validation can use:

```matlab
validate_3d_fullbody("GolfSwing3D_FullBody", struct( ...
    "phase", "scaffold", ...
    "budget", 1000, ...
    "warning_budget", 900, ...
    "report_path", "../output/validation_report.json"))
```

The MATLAB test harness asserts the schema contract when the generated model
exists. Python contract tests validate the report shape and over-budget
failure semantics without requiring MATLAB.
