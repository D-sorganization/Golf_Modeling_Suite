"""Regression tests for issue #4723: package CLI entry point.

The README advertised ``python -m src.shared.python.motion_pipeline``
plus five subcommand modules that were never implemented. This test
file pins the actual contract: a single ``run`` subcommand backed by
``__main__.py``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PACKAGE = "src.shared.python.motion_pipeline"


def _run_module(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", _PACKAGE, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_main_module_help_works() -> None:
    """``python -m motion_pipeline --help`` must exit 0."""
    result = _run_module("--help")
    assert result.returncode == 0, result.stderr
    assert "run" in result.stdout.lower()


def test_run_subcommand_help_lists_engines() -> None:
    result = _run_module("run", "--help")
    assert result.returncode == 0, result.stderr
    out = result.stdout.lower()
    for engine in ("mujoco", "drake", "pinocchio", "opensim"):
        assert engine in out


def test_run_with_unknown_input_exits_nonzero(tmp_path: Path) -> None:
    fake = tmp_path / "no_such_input.c3d"
    result = _run_module("run", str(fake), "--engine", "mujoco")
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "not exist" in combined or "error" in combined


def test_run_with_unknown_engine_exits_nonzero(tmp_path: Path) -> None:
    fake = tmp_path / "input.c3d"
    fake.write_bytes(b"")
    result = _run_module("run", str(fake), "--engine", "nonsense_engine")
    assert result.returncode != 0


def test_no_subcommand_exits_nonzero() -> None:
    result = _run_module()
    assert result.returncode != 0
