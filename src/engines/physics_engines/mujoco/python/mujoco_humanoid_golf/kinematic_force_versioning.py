"""MuJoCo compatibility helpers for kinematic force analysis."""

from __future__ import annotations

import logging
import warnings
from typing import Any


def validate_mujoco_version(
    mujoco_module: Any,
    *,
    minimum_version: tuple[int, int] = (3, 3),
) -> None:
    """Validate that the imported MuJoCo module meets minimum requirements."""
    try:
        version_str = mujoco_module.__version__
        major, minor, *_ = map(int, version_str.split("."))

        if (major, minor) < minimum_version:
            minimum_str = ".".join(str(part) for part in (*minimum_version, 0))
            msg = (
                f"MuJoCo {version_str} detected, but {minimum_str}+ is required.\n"
                "The reshaped Jacobian API (mj_jacBody with 2D arrays) was "
                "introduced in MuJoCo 3.3. Earlier versions use flat arrays "
                "which can cause dimension alignment errors.\n"
                f"Please upgrade: pip install 'mujoco>={minimum_str},<4.0.0'\n"
                "See Issue F-003 in Assessment C for details."
            )
            raise ImportError(msg)

        logging.getLogger(__name__).info(
            "MuJoCo version %s validated successfully",
            version_str,
        )
    except (AttributeError, ValueError) as exc:
        warnings.warn(
            f"Could not validate MuJoCo version: {exc}. "
            "Proceeding with fallback Jacobian handling.",
            category=UserWarning,
            stacklevel=2,
        )
