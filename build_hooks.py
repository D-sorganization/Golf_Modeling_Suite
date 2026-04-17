"""Custom build hooks to bundle UI into Python package."""

import logging
import subprocess
import sys
from os import environ
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

logger = logging.getLogger(__name__)


def _subprocess_error_message(e: subprocess.CalledProcessError) -> str:
    """Extract the most informative message from a CalledProcessError."""
    return e.stderr or e.stdout or str(e)


class UIBuildHook(BuildHookInterface):
    """Build the React UI and include it in the wheel."""

    def _ui_dir(self) -> Path:
        """Return the UI source directory."""
        return Path(self.root) / "ui"

    def _dist_dir(self) -> Path:
        """Return the UI distribution directory."""
        return self._ui_dir() / "dist"

    def _force_build(self) -> bool:
        """Return True if the hook config requests a forced UI rebuild."""
        return bool(self.config.get("force_ui_build"))

    def initialize(self, version: str, build_data: dict) -> None:
        """Initialize build hook."""
        if not (version):
            raise ValueError("Version parameter must not be empty")
        if build_data is None:
            raise ValueError("Build data dictionary must be provided")

        ui_dir = self._ui_dir()
        dist_dir = self._dist_dir()

        # Always skip UI build in CI environment or if explicitly requested
        if environ.get("CI") or environ.get("SKIP_UI_BUILD"):
            logger.warning("Skipping UI build (CI environment or SKIP_UI_BUILD set)")
            if not dist_dir.exists():
                logger.warning("Warning: UI dist directory does not exist!")
            return

        if not dist_dir.exists() or self._force_build():
            logger.info("Building UI...")

            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

            try:
                # Use --legacy-peer-deps to handle potential React version conflicts
                subprocess.run(
                    [npm_cmd, "ci", "--legacy-peer-deps"],
                    cwd=str(ui_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                )

                subprocess.run(
                    [npm_cmd, "run", "build"],
                    cwd=str(ui_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info("UI built successfully to %s", dist_dir)

            except FileNotFoundError:
                msg = "npm not found. Please install Node.js to build the UI."
                logger.error("Error: %s", msg)
                raise RuntimeError(msg) from None

            except subprocess.CalledProcessError as e:
                msg = f"UI build failed: {_subprocess_error_message(e)}"
                logger.error("Error: %s", msg)
                raise RuntimeError(msg) from e

        else:
            logger.info("Using existing UI build at %s", dist_dir)
