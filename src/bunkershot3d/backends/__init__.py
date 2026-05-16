"""Backend drivers for BunkerShot3D."""


class BackendNotImplementedError(NotImplementedError):
    """Raised when a BunkerShot3D backend driver has no real implementation.

    Distinct from a bare ``NotImplementedError`` so callers (and tests) can
    distinguish "this backend is a stub" from "this abstract method has not
    been overridden". The Chrono and LIGGGHTS drivers raise this from
    ``setup()`` until their physics implementations land — see GitHub
    issue #5486 and the per-backend follow-ups linked there.
    """


from .chrono.driver import ChronoDriver  # noqa: E402  (after error class)
from .liggghts.driver import LiggghtsDriver  # noqa: E402
from .mpm.driver import MPMDriver  # noqa: E402

__all__: list[str] = [
    "BackendNotImplementedError",
    "ChronoDriver",
    "LiggghtsDriver",
    "MPMDriver",
]
