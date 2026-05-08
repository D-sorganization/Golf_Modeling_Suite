#!/usr/bin/env python3
"""Entry point for the starting-pose matcher tool.

Run via::

    python -m src.tools.starting_pose_matcher

Or from the unified launcher tile "Starting Pose Matcher".
"""

import sys
from pathlib import Path

# Add the parent directory to the path so relative imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from starting_pose_matcher.gui import main

if __name__ == "__main__":
    sys.exit(main())