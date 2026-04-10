from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock


def _load_setup_module(monkeypatch):
    fake_cx_freeze = types.ModuleType("cx_Freeze")
    fake_cx_freeze.Executable = lambda *args, **kwargs: {
        "args": args,
        "kwargs": kwargs,
    }
    fake_cx_freeze.setup = MagicMock()
    monkeypatch.setitem(sys.modules, "cx_Freeze", fake_cx_freeze)
    sys.modules.pop("installer.windows.setup", None)
    module = importlib.import_module("installer.windows.setup")
    return module, fake_cx_freeze


def test_setup_module_uses_real_src_layout(monkeypatch):
    module, _fake = _load_setup_module(monkeypatch)

    assert module.launchers_assets_dir == module.project_root / "src" / "launchers" / "assets"
    assert module.default_icon_path == module.launchers_assets_dir / "golf_robot_icon.ico"
    assert module.default_icon_path.exists()

    include_files = module.build_include_files()
    assert (str(module.config_dir), "src/config") in include_files
    assert (str(module.shared_urdf_dir), "src/shared/urdf") in include_files
    assert (str(module.launchers_assets_dir), "src/launchers/assets") in include_files
    assert all("shared/icons" not in dest for _, dest in include_files)


def test_setup_main_builds_using_src_paths(monkeypatch):
    module, fake_cx_freeze = _load_setup_module(monkeypatch)
    monkeypatch.setattr(module, "get_available_engines", list)

    assert module.main() == 0
    fake_cx_freeze.setup.assert_called_once()

    kwargs = fake_cx_freeze.setup.call_args.kwargs
    build_exe_options = kwargs["options"]["build_exe"]
    executable_scripts = [item["kwargs"]["script"] for item in kwargs["executables"]]

    assert module.launcher_script.as_posix() in executable_scripts
    assert module.api_script.as_posix() in executable_scripts
    assert (str(module.config_dir), "src/config") in build_exe_options["include_files"]
    assert (
        str(module.launchers_assets_dir),
        "src/launchers/assets",
    ) in build_exe_options["include_files"]
