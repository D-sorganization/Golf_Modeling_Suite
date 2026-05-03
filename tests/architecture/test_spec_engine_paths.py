"""Architecture tests for SPEC component path drift."""

from __future__ import annotations

from pathlib import Path

from scripts.check_spec_paths import validate_spec_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "SPEC.md"


def test_spec_component_paths_exist() -> None:
    """SPEC component and ownership paths must resolve in the repository."""
    violations = validate_spec_paths(REPO_ROOT, SPEC_PATH)

    assert violations == [], "\n".join(str(violation) for violation in violations)


def test_spec_declares_component_path_ownership() -> None:
    """SPEC must document ownership for the path validator contract."""
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    assert "### Component Path Ownership" in spec_text
    assert "`scripts/check_spec_paths.py`" in spec_text
    assert "`tests/architecture/test_spec_engine_paths.py`" in spec_text
