#!/usr/bin/env python3
"""DEPRECATION SHIM — Starting-Pose Matcher has been relocated.

This shim redirects to the canonical location at::

    src/tools/starting_pose_matcher/

The tool has been moved to follow the repository's code organization standards:
- Tools belong in src/tools/, not under engine-specific directories
- The path no longer contains spaces (which caused shell/CI issues)
- Dependencies are now properly declared in pyproject.toml [gui-tools] extra

Usage:
    python -m src.tools.starting_pose_matcher  # canonical path

Or from the unified launcher tile "Starting Pose Matcher".

See issue #4376 for details.
"""

import sys
import warnings
from pathlib import Path

# Issue deprecation warning
warnings.warn(
    "The starting-pose matcher has been relocated from "
    "'src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/apps/golf_gui/"
    "Motion Capture Plotter/' to 'src/tools/starting_pose_matcher/'. "
    "Please update your scripts and launchers to use: "
    "python -m src.tools.starting_pose_matcher",
    DeprecationWarning,
    stacklevel=2,
)

# Add the new location to the path and redirect
here = Path(__file__).parent
repo_root = here.parent.parent.parent.parent.parent.parent.parent.parent.parent
new_location = repo_root / "src" / "tools" / "starting_pose_matcher"

if new_location.exists():
    sys.path.insert(0, str(new_location.parent.parent))
    # Import and run from the new location
    from starting_pose_matcher.gui import main as new_main
    sys.exit(new_main())
else:
    print(f"ERROR: Could not find relocated starting_pose_matcher at {new_location}")
    print("Please reinstall the package with: pip install -e .[gui-tools]")
    sys.exit(1)
