"""Unit tests for CI quality gate scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script_module(name: str):
    script_path = Path(__file__).resolve().parents[2] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_find_print_calls_detects_runtime_print(tmp_path):
    module = _load_script_module("check_no_print_calls")
    file_path = tmp_path / "sample.py"
    file_path.write_text("def run():\n    print('hello')\n", encoding="utf-8")

    lines = module.find_print_calls(file_path)

    assert lines == [2]


def test_file_size_exception_active_handles_valid_and_expired_dates():
    module = _load_script_module("check_file_size_budget")

    assert module._exception_is_active({"expires_on": "2999-01-01"}) is True
    assert module._exception_is_active({"expires_on": "2000-01-01"}) is False


def test_check_root_level_scripts_flags_net_new_root_python_file():
    module = _load_script_module("check_root_level_scripts")

    violations = module.find_disallowed_root_python_files(
        ["new_tool.py", "scripts/new_tool.py", "nested/helper.py"],
        allowlisted={"build_hooks.py"},
    )

    assert violations == ["new_tool.py"]


def test_check_root_level_scripts_ignores_allowlisted_root_python_files():
    module = _load_script_module("check_root_level_scripts")

    violations = module.find_disallowed_root_python_files(
        [
            "build_hooks.py",
            "conftest.py",
            "launch_golf_suite.py",
            ".ci_trigger.py",
        ],
        allowlisted={
            "build_hooks.py",
            "conftest.py",
            "launch_golf_suite.py",
        },
    )

    assert violations == [".ci_trigger.py"]
