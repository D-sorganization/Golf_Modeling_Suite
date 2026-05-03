"""Alembic migration round-trip test.

Verifies that the single migration (0001 initial_schema) can be applied to a
fresh SQLite database via ``alembic upgrade head`` and fully reversed via
``alembic downgrade base`` without error.

Issue #3845: Prevent create_all() from running in production.
"""

import os
import subprocess
from pathlib import Path

import pytest

# Repository root is two parents above tests/integration/
REPO_ROOT = Path(__file__).parents[2]


@pytest.mark.integration
def test_alembic_upgrade_downgrade(tmp_path):
    """Run alembic upgrade head then downgrade base against a temp SQLite DB."""
    db_url = f"sqlite:///{tmp_path}/test.db"

    # Inherit the current environment so that Python path, etc. are available,
    # then override DATABASE_URL so Alembic uses the throwaway database.
    env = {**os.environ, "DATABASE_URL": db_url}

    # ---- upgrade head -------------------------------------------------------
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    # ---- downgrade base -----------------------------------------------------
    result = subprocess.run(
        ["alembic", "downgrade", "base"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic downgrade base failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
