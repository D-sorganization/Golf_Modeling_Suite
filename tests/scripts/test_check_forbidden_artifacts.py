from pathlib import Path

from scripts.check_forbidden_artifacts import find_forbidden_artifacts


def test_find_forbidden_artifacts_reports_root_outputs(tmp_path: Path) -> None:
    assert find_forbidden_artifacts(tmp_path, ["coverage.json"]) == [
        Path("coverage.json")
    ]


def test_find_forbidden_artifacts_reports_jules_completist_data(
    tmp_path: Path,
) -> None:
    assert find_forbidden_artifacts(
        tmp_path, [".jules/completist_data/todo_markers.txt"]
    ) == [Path(".jules/completist_data/todo_markers.txt")]


def test_find_forbidden_artifacts_ignores_unrelated_agent_config(
    tmp_path: Path,
) -> None:
    assert find_forbidden_artifacts(tmp_path, [".agent/skills/lint/SKILL.md"]) == []


def test_find_forbidden_artifacts_reports_backup_file_anywhere(
    tmp_path: Path,
) -> None:
    assert find_forbidden_artifacts(
        tmp_path, ["src/shared/python/__init__.py.bak"]
    ) == [Path("src/shared/python/__init__.py.bak")]


def test_find_forbidden_artifacts_reports_root_pr_body_draft(
    tmp_path: Path,
) -> None:
    assert find_forbidden_artifacts(tmp_path, ["pr_body_3162.md"]) == [
        Path("pr_body_3162.md")
    ]


def test_find_forbidden_artifacts_reports_root_one_shot_fix_script(
    tmp_path: Path,
) -> None:
    assert find_forbidden_artifacts(tmp_path, ["fix_decorators.py"]) == [
        Path("fix_decorators.py")
    ]


def test_find_forbidden_artifacts_allows_scripts_fix_utilities(
    tmp_path: Path,
) -> None:
    assert (
        find_forbidden_artifacts(tmp_path, ["scripts/fix_numpy_compatibility.py"]) == []
    )


def test_find_forbidden_artifacts_reports_ci_trigger_files(
    tmp_path: Path,
) -> None:
    assert find_forbidden_artifacts(tmp_path, [".ci_trigger.py"]) == [
        Path(".ci_trigger.py")
    ]
