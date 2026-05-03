"""MyoSuite physics engine sub-package (experimental tier)."""

import warnings

try:
    import myosuite  # noqa: F401

    from src.engines.physics_engines import ExperimentalTierWarning

    warnings.warn(
        "MyoSuite integration is experimental and unsupported. "
        "API may change without notice.",
        ExperimentalTierWarning,
        stacklevel=2,
    )
except ImportError:
    pass
