import os as _os, sys as _sys

def _should_skip_gui_import() -> bool:
    if _os.environ.get("HEADLESS_CI") == "1":
        return True
    if any("pytest" in _a for _a in _sys.argv) and not _os.environ.get("FORCE_GUI_TESTS"):
        return True
    return False

if _should_skip_gui_import():
    import pytest as _pytest
    _pytest.skip("Skipping GUI tests in headless mode", allow_module_level=True)

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PHYSICS_ENGINE = (
    REPO_ROOT
    / "src"
    / "engines"
    / "physics_engines"
    / "mujoco"
    / "python"
    / "mujoco_humanoid_golf"
    / "physics_engine.py"
)


def test_contact_force_body_lookup_guards_negative_geom_ids() -> None:
    source = PHYSICS_ENGINE.read_text(encoding="utf-8")
    guard = "if contact.geom1 < 0 or contact.geom2 < 0:"
    lookup = "geom1_body = self.model.geom_bodyid[contact.geom1]"

    assert guard in source
    assert source.index(guard) < source.index(lookup)
