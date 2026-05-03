"""Physics engines namespace package.

Organises the Drake, MuJoCo, MyoSuite, OpenSim, Pinocchio and Pendulum
physics-engine sub-packages.  Each sub-package exposes its own public API;
this top-level package is a structural namespace marker only.
"""


class ExperimentalTierWarning(UserWarning):
    """Raised when an experimental-tier physics engine is imported."""
