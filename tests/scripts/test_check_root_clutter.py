from pathlib import Path

from scripts.check_root_clutter import find_disallowed_root_files


def test_find_disallowed_root_files_reports_unapproved_root_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("# ok\n", encoding="utf-8")
    (tmp_path / "foo.py").write_text("print('nope')\n", encoding="utf-8")

    assert find_disallowed_root_files(tmp_path) == [Path("foo.py")]


def test_find_disallowed_root_files_ignores_directories(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()

    assert find_disallowed_root_files(tmp_path) == []


def test_find_disallowed_root_files_reports_unapproved_hidden_file(
    tmp_path: Path,
) -> None:
    (tmp_path / ".ci_trigger.py").write_text("# trigger CI\n", encoding="utf-8")

    assert find_disallowed_root_files(tmp_path) == [Path(".ci_trigger.py")]
