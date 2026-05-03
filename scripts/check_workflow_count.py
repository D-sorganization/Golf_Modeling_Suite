#!/usr/bin/env python3
"""Fail if the number of workflow files in .github/workflows/ exceeds the limit.

CI guard for issue #3835: keep the workflow count at or below 25 to prevent
proliferation of overlapping or redundant automation workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path

MAX_WORKFLOWS = 25
WORKFLOW_DIR = Path(".github") / "workflows"


def count_workflows(workflow_dir: Path) -> list[str]:
    """Return sorted list of .yml files directly inside workflow_dir."""
    if not workflow_dir.is_dir():
        raise FileNotFoundError(f"Workflow directory not found: {workflow_dir}")
    return sorted(p.name for p in workflow_dir.glob("*.yml"))


def main() -> int:
    workflow_files = count_workflows(WORKFLOW_DIR)
    count = len(workflow_files)

    print(f"Workflow count: {count} / {MAX_WORKFLOWS} allowed")

    if count > MAX_WORKFLOWS:
        print(
            f"ERROR: {count} workflow files found in {WORKFLOW_DIR}/ "
            f"but the limit is {MAX_WORKFLOWS}.",
            file=sys.stderr,
        )
        print(
            "Remove or consolidate workflows before adding new ones. "
            "See issue #3835 for the consolidation policy.",
            file=sys.stderr,
        )
        print("\nCurrent workflows:", file=sys.stderr)
        for name in workflow_files:
            print(f"  {name}", file=sys.stderr)
        return 1

    print("Workflow count is within the allowed limit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
