"""Windows MSI installer setup for UpstreamDrift.

This script creates a professional Windows MSI installer with:
- Modular physics engine selection
- Desktop shortcuts and Start Menu entries
- Automatic dependency management
- Uninstaller support
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

try:
    from cx_Freeze import Executable, setup
except ImportError as exc:  # pragma: no cover - exercised in packaging envs
    raise RuntimeError("cx_Freeze is required to build the Windows installer") from exc

_this_file = Path(__file__).resolve()
installer_dir = _this_file.parent
project_root = installer_dir.parent.parent
src_root = project_root / "src"
launchers_assets_dir = src_root / "launchers" / "assets"
config_dir = src_root / "config"
shared_urdf_dir = src_root / "shared" / "urdf"
shared_meshes_dir = src_root / "shared" / "meshes"
default_icon_path = launchers_assets_dir / "golf_robot_icon.ico"
launcher_script = project_root / "launch_golf_suite.py"
api_script = project_root / "start_api_server.py"

# Import version and metadata
try:
    from src.shared.python.core.version import __description__, __version__
except ImportError:
    __version__ = "1.0.0"
    __description__ = "UpstreamDrift - Professional Biomechanical Analysis"

# Define physics engine modules
PHYSICS_ENGINES: dict[str, dict[str, Any]] = {
    "mujoco": {
        "name": "MuJoCo Physics Engine",
        "description": "High-performance physics simulation with contact dynamics",
        "modules": ["mujoco", "engines.physics_engines.mujoco"],
        "required": True,
    },
    "drake": {
        "name": "Drake Manipulation Planning",
        "description": "Trajectory optimization and system analysis",
        "modules": ["pydrake", "engines.physics_engines.drake"],
        "required": False,
    },
    "pinocchio": {
        "name": "Pinocchio Rigid Body Dynamics",
        "description": "Fast rigid body dynamics and derivatives",
        "modules": ["pinocchio", "engines.physics_engines.pinocchio"],
        "required": False,
    },
    "myosuite": {
        "name": "MyoSuite Muscle Simulation",
        "description": "Realistic muscle dynamics and neural control",
        "modules": ["myosuite", "engines.physics_engines.myosuite"],
        "required": False,
    },
    "opensim": {
        "name": "OpenSim Biomechanics",
        "description": "Biomechanical modeling and analysis",
        "modules": ["opensim", "engines.physics_engines.opensim"],
        "required": False,
    },
}

# Base packages always included
BASE_PACKAGES = [
    "numpy",
    "scipy",
    "matplotlib",
    "pandas",
    "PyQt6",
    "yaml",
    "structlog",
    "ezc3d",
    "sympy",
    "defusedxml",
    "shared",
    "launchers",
    "api",
    "tools",
]


def _optional_include(source: Path, destination: str) -> tuple[str, str] | None:
    """Return an include-file tuple only when the source path exists."""
    if source.exists():
        return (str(source), destination)
    return None


def _module_available(module_name: str) -> bool:
    """Check whether an importable module is available without importing it."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def get_available_engines() -> list[str]:
    """Detect which physics engines are available for inclusion."""
    available = []
    missing_required = []

    for engine_id, engine_info in PHYSICS_ENGINES.items():
        main_module = engine_info["modules"][0]
        if _module_available(main_module):
            available.append(engine_id)
        elif engine_info["required"]:
            missing_required.append(main_module)

    if missing_required:
        raise RuntimeError(
            "Required physics engine module(s) missing: "
            + ", ".join(sorted(missing_required))
        )

    return available


def build_include_files() -> list[tuple[str, str]]:
    """Build the package file include list from the real src/ layout."""
    include_files = [
        _optional_include(shared_urdf_dir, "src/shared/urdf"),
        _optional_include(shared_meshes_dir, "src/shared/meshes"),
        _optional_include(launchers_assets_dir, "src/launchers/assets"),
        _optional_include(config_dir, "src/config"),
        _optional_include(project_root / "README.md", "README.md"),
        _optional_include(project_root / "LICENSE", "LICENSE"),
    ]
    return [item for item in include_files if item is not None]


def build_executables() -> list[Executable]:
    """Create frozen executables using the repository entry scripts."""
    return [
        Executable(
            script=str(launcher_script),
            base="Win32GUI",
            target_name="GolfModelingSuite.exe",
            icon=str(default_icon_path),
            shortcut_name="UpstreamDrift",
            shortcut_dir="DesktopFolder",
        ),
        Executable(
            script=str(api_script),
            base="Console",
            target_name="GolfAPI.exe",
            icon=str(default_icon_path),
        ),
    ]


def build_exe_options(available_engines: list[str] | None = None) -> dict[str, Any]:
    """Build cx_Freeze executable options with the discovered engines."""
    if available_engines is None:
        available_engines = get_available_engines()

    packages = list(BASE_PACKAGES)
    for engine_id in available_engines:
        packages.extend(PHYSICS_ENGINES[engine_id]["modules"])

    return {
        "packages": packages,
        "excludes": [
            "tkinter",
            "unittest",
            "pydoc",
            "difflib",
            "calendar",
            "doctest",
            "inspect",
            "pickle",
            "pdb",
            "profile",
            "pstats",
            "timeit",
            "trace",
        ],
        "include_files": build_include_files(),
        "include_msvcrt": True,
        "optimize": 2,
        "build_exe": "build/upstream_drift",
    }


def build_bdist_msi_options() -> dict[str, Any]:
    """Build cx_Freeze MSI options."""
    return {
        "upgrade_code": "{12345678-1234-5678-9012-123456789012}",
        "add_to_path": True,
        "initial_target_dir": r"[ProgramFilesFolder]\UpstreamDrift",
        "install_icon": str(default_icon_path),
        "summary_data": {
            "author": "UpstreamDrift Team",
            "comments": "Professional biomechanical analysis software",
            "keywords": "golf, biomechanics, physics, simulation",
        },
    }


def build_setup_kwargs() -> dict[str, Any]:
    """Assemble the full cx_Freeze setup keyword arguments."""
    return {
        "name": "UpstreamDrift",
        "version": __version__,
        "description": __description__,
        "long_description": """
UpstreamDrift is a professional-grade biomechanical analysis platform
for physics-based modeling and simulation. It provides:

• Multiple physics engines (MuJoCo, Drake, Pinocchio, MyoSuite, OpenSim)
• Video-based pose estimation with MediaPipe
• Ball flight physics with Magnus effect
• Cross-engine validation and comparison
• Professional visualization and analysis tools
• REST API for cloud integration

Perfect for researchers and engineers seeking
research-grade biomechanical insights.
    """.strip(),
        "author": "UpstreamDrift Team",
        "author_email": "support@upstreamdrift.dev",
        "url": "https://github.com/D-sorganization/UpstreamDrift",
        "license": "MIT",
        "executables": build_executables(),
        "options": {
            "build_exe": build_exe_options(),
            "bdist_msi": build_bdist_msi_options(),
        },
        "classifiers": [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.11",
            "Topic :: Scientific/Engineering :: Physics",
            "Operating System :: Microsoft :: Windows",
        ],
    }


def main() -> int:
    """Run the Windows installer build."""
    setup(**build_setup_kwargs())
    return 0


if __name__ == "__main__":
    sys.exit(main())
