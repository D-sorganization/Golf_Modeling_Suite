"""Unit tests for CI quality gate scripts."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_script_module(name: str) -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / f"{name}.py"
    if not script_path.exists():
        script_path = repo_root / "scripts" / "ci" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_find_print_calls_detects_runtime_print(tmp_path) -> None:
    module = _load_script_module("check_no_print_calls")
    file_path = tmp_path / "sample.py"
    file_path.write_text("def run():\n    print('hello')\n", encoding="utf-8")

    lines = module.find_print_calls(file_path)

    assert lines == [2]


def test_file_size_exception_active_handles_valid_and_expired_dates() -> None:
    module = _load_script_module("check_file_size_budget")

    assert module._exception_is_active({"expires_on": "2999-01-01"}) is True
    assert module._exception_is_active({"expires_on": "2000-01-01"}) is False


def test_file_size_budget_script_resolves_repo_root() -> None:
    module = _load_script_module("check_file_size_budget")

    assert module._repo_root() == Path(__file__).resolve().parents[2]


def test_file_size_budget_rejects_exception_growth() -> None:
    module = _load_script_module("check_file_size_budget")
    config = {
        "exceptions": [
            {"path": f"src/file_{index}.py", "owner": "@team", "reason": "split"}
            for index in range(6)
        ]
    }

    active, invalid = module._collect_active_exceptions(config)

    assert active == {}
    assert invalid == ["Too many file-size exceptions: 6 entries (maximum=5)"]


def test_file_size_budget_rejects_long_exception_windows() -> None:
    module = _load_script_module("check_file_size_budget")
    config = {
        "exceptions": [
            {
                "path": "src/large.py",
                "owner": "@team",
                "reason": "split",
                "expires_on": "2026-09-01",
            }
        ]
    }

    active, invalid = module._collect_active_exceptions(
        config, today=module.date(2026, 5, 3)
    )

    assert active == {}
    assert invalid == [
        "Exception window too long: src/large.py "
        "(owner=@team, expires_on=2026-09-01, maximum_days=90)"
    ]


def test_file_size_budget_watchlist_uses_codeowners(tmp_path) -> None:
    module = _load_script_module("check_file_size_budget")
    repo_root = tmp_path
    source_dir = repo_root / "src" / "shared"
    source_dir.mkdir(parents=True)
    watched_file = source_dir / "near_budget.py"
    watched_file.write_text("x = 1\n" * 9, encoding="utf-8")
    codeowners = repo_root / ".github" / "CODEOWNERS"
    codeowners.parent.mkdir()
    codeowners.write_text("/src/ @core\n/src/shared/ @physics-core\n", encoding="utf-8")

    entries = module._collect_watchlist(
        repo_root=repo_root,
        files=[watched_file],
        budget=10,
        codeowners=module._load_codeowners(repo_root),
    )

    assert entries == [
        module.WatchlistEntry(
            path="src/shared/near_budget.py",
            line_count=9,
            owner="@physics-core",
        )
    ]
