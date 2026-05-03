#!/usr/bin/env python3
"""Verify that all GitHub Actions workflow references are pinned to commit SHAs.

This is a thin entry-point that delegates to the canonical implementation in
``scripts/check_github_actions_pinned.py``.  CI can invoke either script; both
enforce the same policy.

Exit codes:
  0 — all external ``uses:`` references contain a 40-character hex SHA.
  1 — one or more references are unpinned (floating tags or branch names).

Lines with a ``# NEEDS-PIN`` comment are intentionally skipped so that
incremental pinning work can land without immediately breaking CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so sibling scripts can be imported
# when this script is invoked directly (e.g. ``python3 scripts/check_actions_pinned.py``).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.check_github_actions_pinned import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
