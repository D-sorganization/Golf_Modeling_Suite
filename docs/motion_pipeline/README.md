# Motion Pipeline — User Workflow Guide

> Part of epic #4558. Make the new pipeline immediately usable by anyone joining the project.

## Quick Start

The motion pipeline processes motion capture data through these stages:

1. **Adapter** - Load source data (C3D, TRC, BVH, JSON, MAT, FBX)
2. **Preprocessing** - Clean, filter, interpolate
3. **Scaling** - Scale skeleton to subject
4. **Inverse Kinematics** - Compute joint angles from markers
5. **Motion Matching** - Refine trajectory via optimization

### CLI Usage

```bash
# Run pipeline on motion capture file
python -m motion_pipeline run <input_file> --engine <engine> --output <output_file>

# Example: Process C3D file with MuJoCo backend
python -m motion_pipeline run capture.c3d --engine mujoco --output result.json

# Example: Process BVH file with Drake backend
python -m motion_pipeline run motion.bvh --engine drake --output drake_result.json
```

### CLI Options

| Option | Description | Default | Choices |
|--------|-------------|---------|---------|
| `source` | Source file path | (required) | - |
| `--engine` | Backend engine | `mujoco` | `mujoco`, `drake`, `pinocchio`, `opensim` |
| `--output` | Output file path | `result.json` | - |
| `--weights` | Cost weights as JSON string | `{}` | - |

### Python API

```python
from motion_pipeline.orchestrator import MotionPipeline, PipelineConfig, AdapterOverride
from pathlib import Path

# Configure pipeline
config = PipelineConfig(
    adapter=AdapterOverride(format="c3d"),
    ik_backend="mujoco",
    matching_backend="mujoco",
)

# Create and run pipeline
pipeline = MotionPipeline(config)
result = pipeline.run(Path("capture.c3d"))

# Access results
if result.success:
    print(f"Matched trajectory: {result.matched_trajectory}")
    print(f"Solve time: {result.solve_time}")
else:
    print(f"Pipeline failed: {result.message}")
```

### REST API

```bash
# Start the API server
python -m motion_pipeline.api

# Or with uvicorn
uvicorn motion_pipeline.api:app --host 0.0.0.0 --port 8000
```

Then use the `/api/v1/motion-pipeline/run` endpoint to upload files and process them.

## Supported Source Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| C3D | `.c3d` | Coordinate 3D motion capture data |
| TRC | `.trc` | Trajectory file format |
| BVH | `.bvh` | Biovision Hierarchy animation |
| JSON | `.json` | Custom JSON format |
| MAT | `.mat` | MATLAB data files |
| FBX | `.fbx` | Autodesk FBX animation |

---

## Next Steps

- [Format Matrix](formats.md) — Auto-generated support matrix for each mocap source
- [Troubleshooting](troubleshooting.md) — Common failure modes and fixes
- [Architecture ADR](../adr/0007-motion-pipeline-architecture.md) — Design decisions and alternatives