import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class DummyHookInterface:
    def __init__(self, root, config):
        self.root = root
        self.config = config


_HATCHLING_MOCKS = {
    "hatchling": MagicMock(),
    "hatchling.builders": MagicMock(),
    "hatchling.builders.hooks": MagicMock(),
    "hatchling.builders.hooks.plugin": MagicMock(),
    "hatchling.builders.hooks.plugin.interface": MagicMock(),
}
_HATCHLING_MOCKS[
    "hatchling.builders.hooks.plugin.interface"
].BuildHookInterface = DummyHookInterface

with patch.dict(sys.modules, _HATCHLING_MOCKS):
    import build_hooks  # noqa: E402


class DummyConfig:
    def __init__(self, root, config=None):
        self.root = root
        self.config = config or {}


def test_ui_build_hook_ci_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CI", "true")
    hook = build_hooks.UIBuildHook(str(tmp_path), {})
    hook.initialize("1.0.0", {})
    # Should skip, no error


def test_ui_build_hook_skip_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SKIP_UI_BUILD", "1")
    hook = build_hooks.UIBuildHook(str(tmp_path), {})
    hook.initialize("1.0.0", {})
    # Should skip, no error


@patch("build_hooks.subprocess.run")
def test_ui_build_hook_builds(mock_run, monkeypatch, tmp_path):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("SKIP_UI_BUILD", raising=False)

    hook = build_hooks.UIBuildHook(str(tmp_path), {})
    hook.initialize("1.0.0", {})

    assert mock_run.call_count == 2
    mock_run.assert_any_call(
        (
            ["npm", "ci", "--legacy-peer-deps"]
            if os.name != "nt"
            else ["npm.cmd", "ci", "--legacy-peer-deps"]
        ),
        cwd=str(tmp_path / "ui"),
        check=True,
        capture_output=True,
        text=True,
    )


@patch("build_hooks.subprocess.run")
def test_ui_build_hook_fails(mock_run, monkeypatch, tmp_path):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("SKIP_UI_BUILD", raising=False)

    mock_run.side_effect = subprocess.CalledProcessError(1, "npm")

    hook = build_hooks.UIBuildHook(str(tmp_path), {})
    with pytest.raises(RuntimeError) as exc:
        hook.initialize("1.0.0", {})

    assert "UI build failed" in str(exc.value)


@patch("build_hooks.subprocess.run")
def test_ui_build_hook_missing_npm(mock_run, monkeypatch, tmp_path):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("SKIP_UI_BUILD", raising=False)

    mock_run.side_effect = FileNotFoundError("npm")

    hook = build_hooks.UIBuildHook(str(tmp_path), {})
    with pytest.raises(RuntimeError) as exc:
        hook.initialize("1.0.0", {})

    assert "npm not found" in str(exc.value)
