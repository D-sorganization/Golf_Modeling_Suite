# Motion Pipeline — User Workflow Guide

> Part of epic #4558. Make the new pipeline immediately usable by anyone joining the project.

## From a mocap file to a tracked motion in one command

This guide walks you through running the UpstreamDrift motion pipeline on
an existing mocap source file (C3D, TRC, BVH, CSV, or one of the JSON
keypoint formats).

> **Note** Earlier drafts of this guide advertised five separate
> commands (`extract_frames`, `pose_estimation`, `lift_3d`, `retarget`,
> `inverse_kinematics`). Those modules were never shipped. The pipeline
> ships as a single composed entry point that runs adapter ->
> preprocessing -> scaling -> IK -> motion-matching for the input file.
> See issue #4723 for the history.

### Quickstart

```bash
python3 -m src.shared.python.motion_pipeline run \
    path/to/capture.c3d \
    --engine mujoco \
    --output result.json
```

Common flags:

| Flag | Meaning |
| ---- | ------- |
| `--engine {mujoco,drake,pinocchio,opensim}` | IK and motion-matching backend. |
| `--source-format c3d` | Override the adapter format. Auto-detected from extension when omitted. |
| `--output result.json` | Write the JSON result here. Defaults to stdout. |
| `--verbose` / `-v` | Enable INFO-level logging. |

The CLI is a thin shim over `MotionPipeline.run()` in
`src/shared/python/motion_pipeline/orchestrator.py`. For programmatic
use, prefer importing the orchestrator directly:

```python
from pathlib import Path
from src.shared.python.motion_pipeline.orchestrator import (
    AdapterOverride,
    MotionPipeline,
    PipelineConfig,
)

config = PipelineConfig(
    adapter=AdapterOverride(format="c3d"),
    ik_backend="mujoco",
    matching_backend="mujoco",
)
result = MotionPipeline(config).run(Path("capture.c3d"))
```

### HTTP API

A FastAPI surface is also available for service deployments:

```bash
uvicorn src.shared.python.motion_pipeline.api:app --host 0.0.0.0 --port 8000
```

| Endpoint | Method | Notes |
| -------- | ------ | ----- |
| `/health` | GET | Returns `{"status": "healthy"}`. |
| `/api/v1/motion-pipeline/run` | POST | Multipart upload + form fields (`source_format`, `ik_backend`, `matching_backend`). |
| `/api/v1/motion-pipeline/run-config` | POST | JSON body matching `PipelineRequest`. |

---

## Worked Example for Each Engine

```bash
# MuJoCo (default — best for contact-rich dynamics)
python3 -m src.shared.python.motion_pipeline run capture.c3d --engine mujoco --output mujoco_result.json

# Drake (trajectory optimization)
python3 -m src.shared.python.motion_pipeline run capture.c3d --engine drake --output drake_result.json

# Pinocchio (fast IK)
python3 -m src.shared.python.motion_pipeline run capture.c3d --engine pinocchio --output pino_result.json

# OpenSim (biomechanics validation)
python3 -m src.shared.python.motion_pipeline run capture.c3d --engine opensim --output osim_result.json
```

---

## When to Choose Each Engine

| Use Case | Recommended Engine | Why |
|----------|-------------------|-----|
| **Contact-rich dynamics** (ground reaction, ball impact) | MuJoCo | Best contact handling, day-to-day development |
| **Trajectory optimization** (finding optimal swing) | Drake | Built-in trajopt solvers, system analysis |
| **Fast IK solutions** (real-time retargeting) | Pinocchio | Optimized rigid-body algorithms |
| **Biomechanics validation** | OpenSim | Gold-standard musculoskeletal models |
| **Muscle dynamics** | MyoSuite | Detailed muscle activation modeling |

---

## Next Steps

- [Format Matrix](formats.md) — Auto-generated support matrix for each mocap source
- [Troubleshooting](troubleshooting.md) — Common failure modes and fixes
- [Architecture ADR](../adr/0007-motion-pipeline-architecture.md) — Design decisions and alternatives
