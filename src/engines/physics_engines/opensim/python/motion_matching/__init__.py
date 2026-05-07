"""OpenSim motion-matching helpers.

Pure-Python utilities that bridge the OpenSim Rajagopal2015-derived model
to the canonical Simscape 25-DOF body chain. None of the modules here
import the ``opensim`` SWIG wrapper, so they run on every CI lane (the
heavy ``opensim`` extra is only required by the validation test marked
``pytest.mark.requires_opensim``).
"""

from __future__ import annotations

from .coord_map import (  # noqa: F401
    OPENSIM_COORD_ORDER,
    OPENSIM_NEUTRAL_POSE,
    OPENSIM_SIGN_CONVENTION,
    OPENSIM_TO_SIMSCAPE,
    SIMSCAPE_COORD_ORDER,
    frame_y_up_to_z_up,
    frame_z_up_to_y_up,
    from_simscape,
    quat_canonical_to_eigen,
    quat_eigen_to_canonical,
    to_simscape,
)

__all__ = [
    "OPENSIM_COORD_ORDER",
    "OPENSIM_NEUTRAL_POSE",
    "OPENSIM_SIGN_CONVENTION",
    "OPENSIM_TO_SIMSCAPE",
    "SIMSCAPE_COORD_ORDER",
    "frame_y_up_to_z_up",
    "frame_z_up_to_y_up",
    "from_simscape",
    "quat_canonical_to_eigen",
    "quat_eigen_to_canonical",
    "to_simscape",
]
