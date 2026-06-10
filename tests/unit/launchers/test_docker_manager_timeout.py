"""Regression coverage for Docker build timeout handling."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.launchers.docker_manager import DockerBuildThread

pytestmark = pytest.mark.unit


class BlockingStdout:
    """Stdout fake that remains open until closed by process cleanup."""

    def __init__(self) -> None:
        self._closed = threading.Event()

    def readline(self) -> str:
        self._closed.wait()
        return ""

    def close(self) -> None:
        self._closed.set()


class TimeoutProcess:
    """Popen fake whose stdout never reaches EOF before the process timeout."""

    pid = 4242
    returncode = None

    def __init__(self) -> None:
        self.stdout = BlockingStdout()
        self.args = ["docker", "build"]
        self.wait_timeouts: list[float | None] = []
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        raise subprocess.TimeoutExpired(cmd=["docker", "build"], timeout=timeout)

    def kill(self) -> None:
        self.killed = True
        self.stdout.close()


@patch("subprocess.Popen")
@patch.object(Path, "exists", return_value=True)
def test_docker_build_timeout_is_enforced_while_stdout_is_open(
    _mock_exists: MagicMock,
    mock_popen: MagicMock,
) -> None:
    process = TimeoutProcess()
    mock_popen.return_value = process

    thread = DockerBuildThread(
        target_stage="all",
        image_name="test_image",
        context_path=Path("/fake/context"),
        build_timeout_seconds=0.01,
    )
    finished = MagicMock()
    thread.finished_signal.connect(finished)

    with patch("src.launchers.docker_manager.kill_process_tree") as kill_tree:
        kill_tree.side_effect = lambda pid: process.stdout.close() or True

        thread.run()

    assert 0 < process.wait_timeouts[0] <= 0.01
    kill_tree.assert_called_once_with(process.pid)
    assert process.killed is False
    finished.assert_called_once_with(False, "Build timed out (exceeded 1 hour limit)")
