"""
Project Chrono backend driver for BunkerShot3D.

This driver is currently a stub. Calling :py:meth:`ChronoDriver.setup`
or :py:meth:`ChronoDriver.run` will raise
:class:`bunkershot3d.backends.BackendNotImplementedError`. The original
empty implementation silently produced no output, so callers were
unable to tell a real run apart from a no-op. Failing loudly preserves
that signal until the real Chrono implementation lands.

Tracked: https://github.com/D-sorganization/UpstreamDrift/issues/5486
"""

from pathlib import Path

from bunkershot3d.backends import BackendNotImplementedError
from bunkershot3d.config import BunkerShotConfig


_NOT_IMPLEMENTED_MESSAGE = (
    "Chrono backend is not yet implemented; "
    "see GitHub issue #5486 for the per-backend follow-up."
)


class ChronoDriver:
    """Driver for running the bunker shot simulation using Project Chrono."""

    def __init__(self, config_path: Path | str) -> None:
        self.config_path = Path(config_path)
        self.config = BunkerShotConfig.from_yaml(self.config_path)

    def setup(self) -> None:
        """Setup the Chrono system (grains, clubhead, constraints).

        Raises
        ------
        BackendNotImplementedError
            Always — the Chrono backend is a stub. Tracked via #5486.
        """
        raise BackendNotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def run(self, output_path: Path | str) -> None:
        """Run the simulation and write HDF5 output.

        Raises
        ------
        BackendNotImplementedError
            Always — the Chrono backend is a stub. Tracked via #5486.
        """
        # Delegate to ``setup`` so the same error message is surfaced
        # whether a caller invokes ``setup`` directly or jumps straight
        # to ``run``. DRY: one source of truth for the message.
        self.setup()
