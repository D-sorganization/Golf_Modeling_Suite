"""
LIGGGHTS backend driver for BunkerShot3D.

This driver is currently a stub. The previous implementation wrote a
placeholder input deck that contained no geometry, executed LIGGGHTS
on it, and silently swallowed any failure — so callers had no signal
that the simulation had not actually run. The driver now fails loudly
from :py:meth:`setup` until the real LIGGGHTS implementation lands.

Tracked: https://github.com/D-sorganization/UpstreamDrift/issues/5486
"""

from pathlib import Path

from bunkershot3d.backends import BackendNotImplementedError
from bunkershot3d.config import BunkerShotConfig


_NOT_IMPLEMENTED_MESSAGE = (
    "LIGGGHTS backend is not yet implemented; "
    "see GitHub issue #5486 for the per-backend follow-up."
)


class LiggghtsDriver:
    """Driver for running the bunker shot simulation using LIGGGHTS."""

    def __init__(self, config_path: Path | str) -> None:
        self.config_path = Path(config_path)
        self.config = BunkerShotConfig.from_yaml(self.config_path)

    def setup(self) -> None:
        """Set up the LIGGGHTS work directory and input deck.

        Raises
        ------
        BackendNotImplementedError
            Always — the LIGGGHTS backend is a stub. Tracked via #5486.
        """
        raise BackendNotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def run(self, output_path: Path | str) -> None:
        """Run the simulation via subprocess and parse dump output into HDF5.

        Raises
        ------
        BackendNotImplementedError
            Always — the LIGGGHTS backend is a stub. Tracked via #5486.
        """
        # Delegate to ``setup`` for a single source of truth on the
        # not-implemented message (DRY).
        self.setup()
