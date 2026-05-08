#!/usr/bin/env python3
"""Compatibility shim for the relocated Starting-Pose Matcher GUI.

The canonical entry point is now::

    python -m src.tools.starting_pose_matcher

This file remains so existing scripts that run ``python starting_pose_matcher.py``
from the legacy Simscape GUI directory continue to launch the relocated tool.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "src" / "tools" / "starting_pose_matcher").is_dir():
            return candidate
    msg = "Could not find relocated starting_pose_matcher under src/tools/"
    raise RuntimeError(msg)


def _add_import_roots(repo_root: Path) -> None:
    """Expose both ``src.*`` and ``tools.*`` imports for the relocated GUI."""
    for path in (repo_root, repo_root / "src"):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)


def main() -> int:
    warnings.warn(
        "The starting-pose matcher has moved to 'src/tools/starting_pose_matcher/'. "
        "Use: python -m src.tools.starting_pose_matcher",
        DeprecationWarning,
        stacklevel=2,
    )

    here = Path(__file__).resolve().parent
    repo_root = _find_repo_root(here)
    _add_import_roots(repo_root)

    from tools.starting_pose_matcher.gui import main as relocated_main

    return relocated_main()


if __name__ == "__main__":
    sys.exit(main())
