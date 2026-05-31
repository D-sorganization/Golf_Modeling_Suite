"""License-ledger coverage checks for direct dependency declarations."""

from __future__ import annotations

from pathlib import Path

from scripts.legal.check_license_ledger import (
    declared_dependency_names,
    ledger_package_names,
    validate_license_ledger,
)


ROOT = Path(__file__).resolve().parents[3]


def test_license_ledger_covers_declared_dependencies() -> None:
    """Every direct dependency in pyproject.toml must have a ledger row."""
    declared = declared_dependency_names(ROOT / "pyproject.toml")
    ledgered = ledger_package_names(ROOT / "docs" / "legal" / "licenses.md")

    assert declared <= ledgered


def test_license_ledger_flags_openpose_as_non_commercial_opt_in() -> None:
    """OpenPose must stay visibly fenced for commercial builds."""
    ledger = (ROOT / "docs" / "legal" / "licenses.md").read_text(encoding="utf-8")

    assert "`openpose`" in ledger
    assert "Non-commercial" in ledger
    assert "Opt-in" in ledger


def test_license_ledger_script_reports_clean() -> None:
    """The advisory script must share the same contract as CI/tests."""
    errors = validate_license_ledger(
        pyproject_path=ROOT / "pyproject.toml",
        ledger_path=ROOT / "docs" / "legal" / "licenses.md",
    )

    assert errors == []
