"""OpenSim physics engine sub-package (experimental tier)."""

import warnings

try:
    import opensim  # noqa: F401

    from src.engines.physics_engines import ExperimentalTierWarning

    warnings.warn(
        "OpenSim integration is experimental and unsupported. "
        "API may change without notice.",
        ExperimentalTierWarning,
        stacklevel=2,
    )
except ImportError:
    pass
