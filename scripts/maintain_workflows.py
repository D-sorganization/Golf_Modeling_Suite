"""Workflow maintenance helper.

This file intentionally fails loudly instead of pretending to refactor workflows.
The previous placeholder implementation performed no work and exited successfully,
which made automation believe workflows had been updated when they had not.
"""

from __future__ import annotations

from pathlib import Path

from scripts.script_utils import run_main, setup_script_logging

logger = setup_script_logging(__name__)


def refactor_workflow(filepath: str | Path) -> None:
    """Refactor a GitHub Actions workflow file.

    This implementation is intentionally not provided yet.
    """

    raise NotImplementedError(
        "Workflow refactoring is not implemented yet; this script now fails loudly "
        "instead of silently doing nothing."
    )


def main() -> int:
    """Entry point for the workflow maintenance script."""

    logger.error(
        "scripts/maintain_workflows.py is currently a placeholder and does not "
        "modify workflows. Use a dedicated workflow editor before re-enabling it."
    )
    return 1


if __name__ == "__main__":
    run_main(main, logger)
