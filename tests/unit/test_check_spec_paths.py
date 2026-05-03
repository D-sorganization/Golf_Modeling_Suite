"""Unit tests for the SPEC path validation script."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_script_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "check_spec_paths.py"
    spec = importlib.util.spec_from_file_location("check_spec_paths", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extracts_component_and_ownership_paths() -> None:
    module = _load_script_module()
    spec_text = """
### Key Components

| Component | Location | Purpose |
| --- | --- | --- |
| MuJoCo Engine Adapter | `src/engines/physics_engines/mujoco/python/physics.py` | Adapter |
| API | `src/api/` | Backend |

### Component Path Ownership

| Path | Owner | Validation |
| --- | --- | --- |
| `scripts/check_spec_paths.py` | Architecture | CI path guard |

## 5. Desired Functionality
"""

    paths = module.extract_spec_paths(spec_text)

    assert paths == [
        module.SpecPath("src/engines/physics_engines/mujoco/python/physics.py"),
        module.SpecPath("src/api/"),
        module.SpecPath("scripts/check_spec_paths.py"),
    ]


def test_validate_spec_paths_reports_missing_file(tmp_path: Path) -> None:
    module = _load_script_module()
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text(
        """
### Key Components

| Component | Location | Purpose |
| --- | --- | --- |
| Missing | `src/missing.py` | Should fail |
""",
        encoding="utf-8",
    )

    violations = module.validate_spec_paths(tmp_path, spec_path)

    assert violations == [
        module.SpecPathViolation("src/missing.py", "documented path does not exist")
    ]


def test_validate_spec_paths_enforces_directory_marker(tmp_path: Path) -> None:
    module = _load_script_module()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "api").mkdir()
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text(
        """
### Key Components

| Component | Location | Purpose |
| --- | --- | --- |
| API | `src/api` | Missing trailing slash for a directory |
""",
        encoding="utf-8",
    )

    violations = module.validate_spec_paths(tmp_path, spec_path)

    assert violations == [
        module.SpecPathViolation("src/api", "directory paths must end with /")
    ]
