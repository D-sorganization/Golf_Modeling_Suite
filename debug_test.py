import sys
import numpy as np

from tests.integration.test_urdf_cross_engine_fk import compute_mujoco_fk, compute_drake_fk, _generate_configs
from pathlib import Path

urdf_path = Path("/tmp/pytest-of-jules/pytest-4/cross_engine_fk0/humanoid.urdf")
if not urdf_path.exists():
    import tempfile
    import os
    print("Could not find urdf path, searching...")
    # Actually just run the test directly via pytest but printing shapes and diffs
