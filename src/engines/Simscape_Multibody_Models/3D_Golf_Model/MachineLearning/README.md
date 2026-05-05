# Machine Learning Dynamics Surrogate

This folder contains the first supervised-learning pipeline for the 3D MATLAB/Simscape golf swing model.

Goal:

```text
[joint positions, joint velocities, applied torques/forces] -> [joint positions, joint velocities, joint/segment accelerations]
```

Each parquet row is treated as one independent dynamics sample. Time is excluded
from training and should be treated only as a sample ordering or sample ID field
when reconstructing a swing outside the supervised dataset.

The companion club-control strategy is documented in `CONTROL_STRATEGY.md`.

## Files

- `column_manifest_inverse_ready.json` defines the current no-time column selection.
- `column_manifest.json` and `column_manifest_expanded.json` preserve earlier column selections.
- `extract_dynamics_dataset.py` projects the 9 GB source parquet into a compact numeric parquet.
- `extract_club_datasets.py` creates direct torque-to-club and body-to-club datasets.
- `prepare_club_target_trajectory.py` converts the measured TW/GW workbook sheets into club target CSV files.
- `slice_club_target.py` creates full-swing or downswing-only target trajectories.
- `calibrate_club_target_to_sim.py` fits measured club coordinates into the Simscape club-log frame.
- `compare_simulated_club_motion.py` reports target-vs-simulated club motion error and can write a comparison plot.
- `create_reference_body_state.py` writes a seed body-state CSV for club inverse optimization.
- `train_dynamics_surrogate.py` trains a PyTorch MLP on the reduced parquet.
- `optimize_torque_sequence_for_club.py` optimizes a torque timeseries against a measured club target.
- `optimize_torques_for_desired_kinematics.py` starts the inverse-control phase by optimizing torque inputs against the trained forward surrogate.
- `optimize_body_kinematics_for_club.py` starts the two-stage club-control phase by finding body kinematics that match a desired club state.
- `export_torque_polynomials.py` converts optimized torque timeseries into MATLAB sixth-order polynomial coefficient MAT files.
- `matlab/run_ml_polynomial_input_swing.m` loads those coefficients and runs `GolfSwing3D_Kinetic`.
- `matlab/export_start_state_from_input_file.m` exports address or top-of-backswing start positions/velocities into a separate MAT file.
- `matlab/export_simulated_club_csv.m` writes Simscape club-head logs to CSV for calibration and comparison.
- `matlab/ml_workflow_gui.m` provides a GUI for the full workflow.
- `CONTROL_STRATEGY.md` documents the one-stage and two-stage control approaches, commands, and current metrics.
- `data/processed/` is the default generated-data output location.
- `runs/` is the default model/checkpoint output location.

Generated data and model artifacts are intentionally ignored by git.

## Why These Columns

The current model keeps the broad kinematic logs so the learned state/output
space is useful for the inverse-control phase.

Inputs:

- joint angular/translation positions
- joint angular/translation velocities
- `*ActuatorTorque*`
- hip translation force inputs
- hip torque inputs

Targets:

- joint angular/translation positions
- joint angular/translation velocities
- joint/segment acceleration columns

Excluded from inputs:

- `time`
- constraint forces/torques
- local reaction forces/torques
- hand/club reaction force outputs
- `model_*` constants

Those excluded columns are useful for diagnostics, but many are solver outputs or reaction quantities and can leak target information into the model.

## Extract The Reduced Dataset

From the repository root:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\extract_dynamics_dataset.py `
  --source C:\Users\diete\Repositories\data\TenThousandFiles.parquet `
  --manifest src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\column_manifest_inverse_ready.json `
  --output src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\golf_inverse_ready.parquet
```

Default output:

```text
src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\golf_inverse_ready.parquet
```

The source parquet stores all numeric values as strings, so extraction casts selected columns to `float32`.

## Train

Use Python 3.12. The current global Python 3.13 Torch install on this machine failed to import during inspection.

CPU smoke run:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\train_dynamics_surrogate.py `
  --epochs 10 `
  --batch-size 8192
```

CUDA setup for the 12 GB NVIDIA machine should use a clean venv with a CUDA-enabled PyTorch wheel:

```powershell
py -3.12 -m venv .venv-golf-ml
.\.venv-golf-ml\Scripts\python -m pip install --upgrade pip
.\.venv-golf-ml\Scripts\python -m pip install numpy pyarrow scikit-learn tqdm
.\.venv-golf-ml\Scripts\python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
.\.venv-golf-ml\Scripts\python src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\train_dynamics_surrogate.py `
  --epochs 100 `
  --batch-size 8192 `
  --device cuda
```

If `cu128` is not compatible with the installed NVIDIA driver, use the PyTorch selector for the installed driver/CUDA runtime and keep the same script command.

## Inverse-Control Direction

The trained network is a forward surrogate:

```text
f(position, velocity, torque) = predicted next/sample position, velocity, acceleration
```

The next control layer should solve the inverse problem by optimizing the torque
inputs while holding the measured/current position and velocity fixed:

```text
argmin_torque || f(current_position, current_velocity, torque) - desired_kinematic_state ||
```

That is usually better than training a direct inverse network first, because the
same desired acceleration can be feasible through different torque combinations
and actuator constraints. The first inverse phase should load `best_model.pt`,
standardize candidate inputs with the saved scalers, optimize torque variables
with bounds/regularization, and emit a timeseries of torques for the MATLAB model.

The initial utility is sample-based:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\optimize_torques_for_desired_kinematics.py `
  --checkpoint src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\runs\inverse_ready_10_cpu\best_model.pt `
  --current-state current_state.json `
  --desired-state desired_state.json `
  --output optimized_torques.json
```

For a full swing, run this per sample in the desired trajectory, then smooth and
bound the resulting torque series before applying it back to the Simscape model.

## Club-Only Target Direction

When full-body motion capture is unavailable, use the measured club trajectory
as the target. The located workbook is:

```text
src\engines\Simscape_Multibody_Models\3D_Golf_Model\matlab\src\apps\golf_gui\Motion Capture Plotter\Wiffle_ProV1_club_3D_data.xlsx
```

Prepare the `TW_ProV1` target trajectory:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\prepare_club_target_trajectory.py `
  --sheet TW_ProV1 `
  --output src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_club_target.csv
```

Create a scenario target. Use `full-swing` for the full measured motion or
`downswing` when starting the model at the top of backswing:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\slice_club_target.py `
  --input-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_club_target.csv `
  --output-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_downswing_club_target.csv `
  --scenario downswing `
  --reset-time
```

Extract the club surrogate datasets:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\extract_club_datasets.py `
  --mode both
```

Train the direct torque-to-club model:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\train_dynamics_surrogate.py `
  --dataset src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\club_direct_dynamics.parquet `
  --output-dir src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\runs\club_direct_10_cpu `
  --epochs 10 `
  --batch-size 8192
```

Train the body-to-club model:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\train_dynamics_surrogate.py `
  --dataset src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\body_to_club_kinematics.parquet `
  --output-dir src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\runs\body_to_club_10_cpu `
  --epochs 10 `
  --batch-size 8192
```

## Torque Polynomial Export For MATLAB

The Simscape model already uses sixth-order polynomial input functions:

```text
A*x^6 + B*x^5 + C*x^4 + D*x^3 + E*x^2 + F*x + G
```

The ML bridge optimizes a torque timeseries, fits one sixth-order polynomial per
controlled joint axis, and writes scalar MATLAB variables such as `LSInputXA`,
`LSInputXB`, ..., `LSInputXG`.

Create a seed body state from the extracted simulator data:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\create_reference_body_state.py `
  --dataset src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\club_direct_dynamics.parquet `
  --output src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\reference_body_state.csv
```

Optimize torques for the prepared club trajectory:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\optimize_torque_sequence_for_club.py `
  --checkpoint src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\runs\club_direct_10_cpu\best_model.pt `
  --desired-club-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_club_target.csv `
  --reference-body-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\reference_body_state.csv `
  --output-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\optimized_club_torques.csv
```

Fit MATLAB polynomial coefficients:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\export_torque_polynomials.py `
  --torque-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\optimized_club_torques.csv `
  --output-mat src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\ml_torque_polynomial_inputs.mat
```

Run MATLAB with those coefficients:

```matlab
cd('C:\Users\diete\Repositories\UpstreamDrift\src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning')
addpath(fullfile(pwd, 'matlab'))
export_start_state_from_input_file( ...
    "downswing", ...
    fullfile(pwd, 'data', 'processed', 'ml_downswing_start_state.mat'));
simOut = run_ml_polynomial_input_swing( ...
    fullfile(pwd, 'data', 'processed', 'ml_torque_polynomial_inputs.mat'), ...
    'GolfSwing3D_Kinetic', ...
    fullfile(pwd, 'data', 'processed', 'ml_downswing_start_state.mat'));
export_simulated_club_csv( ...
    simOut, ...
    fullfile(pwd, 'data', 'processed', 'simulated_club_motion.csv'));
```

Calibrate the measured target into the Simscape club-log frame after a baseline
or replay simulation is available:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\calibrate_club_target_to_sim.py `
  --target-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_downswing_club_target.csv `
  --sim-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\simulated_club_motion.csv `
  --output-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_downswing_club_target_calibrated.csv `
  --output-json src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\club_target_calibration.json
```

Compare the simulated motion to the calibrated desired target:

```powershell
py -3.12 src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\compare_simulated_club_motion.py `
  --target-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\TW_ProV1_downswing_club_target_calibrated.csv `
  --sim-csv src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\simulated_club_motion.csv `
  --output-json src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\club_motion_comparison.json `
  --output-png src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning\data\processed\club_motion_comparison.png
```

## GUI Workflow

Open the MATLAB GUI from the ML folder:

```matlab
cd('C:\Users\diete\Repositories\UpstreamDrift\src\engines\Simscape_Multibody_Models\3D_Golf_Model\MachineLearning')
addpath(fullfile(pwd, 'matlab'))
ml_workflow_gui
```

The GUI exposes the same steps as the scripts: prepare target, slice full swing
or downswing, calibrate target coordinates, export the scenario start state,
optimize torques, export sixth-order polynomial inputs, run the Simscape model,
and compare the generated club motion against the target.

## Expected Runtime

The reduced dataset is only 310,000 rows and about 160 numeric columns, so the training estimate changes a lot.

On the 12 GB GPU, a baseline MLP should train in minutes, not hours, once CUDA PyTorch is installed. Expect roughly:

- extraction: a few minutes, mostly parquet/string decoding overhead
- 5-epoch smoke run: under a minute on GPU, a few minutes on CPU
- 100-epoch baseline: roughly 5-20 minutes on the 12 GB GPU, depending on CUDA setup and batch size

The original multi-hour estimate only applies if training directly from the full wide parquet or using a much larger temporal model/hyperparameter sweep.
