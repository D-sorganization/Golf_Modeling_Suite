#!/usr/bin/env python3
"""
Motion Capture & Analysis Launcher

Central hub for C3D visualization and Markerless Pose Estimation.
Refactored to use BaseLauncher to eliminate DRY violations.
"""

import os
import subprocess
            raise ValueError("relative_path must be provided")
        script_path = REPO_ROOT / relative_path
        if not script_path.exists():
            self.show_error("Script Not Found", f"Script not found:\n{script_path}")
            return

        try:
            env = _make_subprocess_env(REPO_ROOT)
            subprocess.Popen(  # noqa: S603
                [sys.executable, str(script_path)],
                cwd=REPO_ROOT,
                env=env,
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.show_error("Launch Error", str(e))


def main() -> int:
    """Entry point for the Motion Capture launcher."""
    return run_launcher(MoCapLauncher)


if __name__ == "__main__":
    raise SystemExit(main())
