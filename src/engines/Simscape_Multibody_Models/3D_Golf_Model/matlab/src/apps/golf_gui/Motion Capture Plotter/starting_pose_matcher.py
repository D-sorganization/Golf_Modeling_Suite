"""DEPRECATED — relocated to ``src.tools.starting_pose_matcher.gui``.

This shim re-exports the main entrypoint so any sibling code or test
fixture that still imports or runs ``starting_pose_matcher`` from this directory
keeps working through one release cycle.  See issue #4376.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "starting_pose_matcher at this path is deprecated.  Import or run from "
    "``src.tools.starting_pose_matcher`` instead.  See issue #4376.",
    DeprecationWarning,
    stacklevel=2,
)

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_repo_root = Path(__file__).resolve().parents[6]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.tools.starting_pose_matcher.gui import (  # noqa: E402
    main,
)

if __name__ == "__main__":
    sys.exit(main())
