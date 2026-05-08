# Starting Pose Matcher

A professional-grade alignment tool for matching Simscape multibody golfer models to motion-capture data.

## Overview

This tool solves for a 7-DOF rigid transform (translation, rotation, scale) that minimizes the error between a Simscape model skeleton and motion-capture target data. The resulting transform seeds optimization pipelines like `fit_swing_full_pipeline`.

## Installation

```bash
pip install upstream-drift[gui-tools]
```

The `gui-tools` extra installs PyQt6, matplotlib, pandas, and openpyxl dependencies.

## Usage

### From Command Line

```bash
python -m src.tools.starting_pose_matcher
```

### From Unified Launcher

Select the "Starting Pose Matcher" tile in the unified launcher interface.

## Features

- **Mocap Loading**: Load Wiffle-style xlsx motion-capture files with automatic unit conversion (cm→m)
- **Event Detection**: Automatic event header parsing (Address, Top of Backswing, Impact, Finish)
- **Two-Point Shaft Snap**: Solves Rz + translation so the model shaft aligns with mocap shaft
- **7-DOF Transform**: Manual control over Tx, Ty, Tz, Rx, Ry, Rz, and scale
- **Real-time Visualization**: 3D matplotlib visualization with camera presets
- **Playback**: Animate mocap and/or skeleton trajectories
- **Session Save/Load**: Complete UI state persistence

## Workflow

1. Load motion-capture xlsx file (default: `Wiffle_ProV1_club_3D_data.xlsx`)
2. Select pose skeletons to display (Top of Backswing, Impact)
3. Use "Snap" buttons for automatic shaft alignment
4. Fine-tune with manual transform controls
5. Save offsets to JSON for use in optimization pipelines

## File Structure

```
starting_pose_matcher/
├── __init__.py          # Package exports
├── __main__.py          # Entry point
├── core.py              # Pure math + dataclasses (testable without Qt)
├── gui.py               # PyQt6 QMainWindow interface
├── skeleton_provider.py # Skeleton format abstraction layer
└── README.md            # This file
```

## Dependencies

- PyQt6
- matplotlib
- pandas
- openpyxl
- numpy

## Related Issues

- Issue #4376: Relocate starting-pose-matcher to src/tools/
- Issue #4367: Port to MuJoCo/Drake/Pinocchio via SkeletonProvider

## Migration Note

This package was relocated from:
```
src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/Motion Capture Plotter/
```

A deprecation shim remains at the old path that redirects to this package.