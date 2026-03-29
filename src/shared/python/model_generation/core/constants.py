"""
Physical and default constants for model generation.

This module provides centralized constants used throughout
the model_generation package.
"""

from __future__ import annotations

import math

# =============================================================================
# Physical Constants
# =============================================================================

# Standard gravity (m/s^2)
GRAVITY_M_S2: float = 9.80665

# Human tissue average density (kg/m^3)
# Approximately the density of muscle tissue
TISSUE_DENSITY_KG_M3: float = 1050.0

# Water density for reference (kg/m^3)
WATER_DENSITY_KG_M3: float = 1000.0

# Bone density (kg/m^3)
BONE_DENSITY_KG_M3: float = 1900.0

# Fat tissue density (kg/m^3)
FAT_DENSITY_KG_M3: float = 900.0

# =============================================================================
# Default Values
# =============================================================================

# Default density for mesh-based inertia calculation (kg/m^3)
DEFAULT_DENSITY_KG_M3: float = TISSUE_DENSITY_KG_M3

# Default inertia value when not specified (kg*m^2)
# Retained as a generic fallback; prefer estimate_default_inertia() below.
DEFAULT_INERTIA_KG_M2: float = 0.1


def estimate_default_inertia(mass: float | None = None) -> float:
    """Estimate a reasonable default inertia from body mass.

    Models the body as a uniform sphere and computes I = (2/5)*m*r^2
    where r is derived from the mass assuming tissue density (~1050 kg/m^3).
    This avoids over-estimating inertia for small/light bodies.

    For a 1 kg body: I ~ 0.004 kg*m^2  (reasonable for a hand segment)
    For a 10 kg body: I ~ 0.046 kg*m^2  (reasonable for a thigh segment)
    For a 75 kg body: I ~ 0.71 kg*m^2   (full-body order of magnitude)

    Args:
        mass: Body mass in kg. If None or <= 0, returns DEFAULT_INERTIA_KG_M2.

    Returns:
        Estimated moment of inertia in kg*m^2, clamped to [MIN_INERTIA_KG_M2, 10.0].
    """
    if mass is None or mass <= 0:
        return DEFAULT_INERTIA_KG_M2

    import math

    density = TISSUE_DENSITY_KG_M3  # ~1050 kg/m^3
    # Radius of equivalent uniform sphere: V = m/rho, V = 4/3*pi*r^3
    radius = (3.0 * mass / (4.0 * math.pi * density)) ** (1.0 / 3.0)
    # Moment of inertia of uniform sphere: I = 2/5 * m * r^2
    inertia = 0.4 * mass * radius**2
    # Clamp to a reasonable range
    return max(MIN_INERTIA_KG_M2, min(inertia, 10.0))


# Default minimum mass for intermediate/virtual links (kg)
# Small but non-zero to avoid numerical issues
INTERMEDIATE_LINK_MASS: float = 0.001

# =============================================================================
# Joint Defaults
# =============================================================================

# Default joint damping coefficient (N*m*s/rad)
# Retained as a generic fallback; prefer JOINT_DAMPING_TABLE below.
DEFAULT_JOINT_DAMPING: float = 0.5

# Joint-type-specific damping coefficients (N*m*s/rad).
# Values are order-of-magnitude estimates scaled to joint size and typical
# biological/mechanical loading:
#   - Large joints (hip, knee, shoulder): 1.0-2.0 N*m*s/rad
#   - Medium joints (elbow, ankle, wrist): 0.3-0.5 N*m*s/rad
#   - Small joints (finger, toe, neck sub-joints): 0.05-0.1 N*m*s/rad
# Reference: Winters & Stark, "Estimated Mechanical Properties of
# Synergistically Acting Agonist-Antagonist Muscle Groups",
# J. Biomechanics, Vol. 21, No. 12, 1988, pp. 1027-1041.
JOINT_DAMPING_TABLE: dict[str, float] = {
    # Large joints
    "hip": 1.5,
    "knee": 1.5,
    "shoulder": 1.0,
    # Medium joints
    "elbow": 0.5,
    "ankle": 0.4,
    "wrist": 0.3,
    # Small joints
    "finger": 0.05,
    "toe": 0.05,
    "neck": 0.1,
    # Spine segments
    "lumbar": 0.8,
    "thoracic": 0.6,
}


def get_joint_damping(joint_name: str) -> float:
    """Return damping coefficient for a joint, scaling by joint type/size.

    Matches joint_name against known joint types in JOINT_DAMPING_TABLE.
    Falls back to DEFAULT_JOINT_DAMPING if no match is found.

    Args:
        joint_name: Name of the joint (e.g. "left_hip", "r_elbow_flexion").

    Returns:
        Damping coefficient in N*m*s/rad.
    """
    name_lower = joint_name.lower()
    for joint_type, damping in JOINT_DAMPING_TABLE.items():
        if joint_type in name_lower:
            return damping
    return DEFAULT_JOINT_DAMPING


# Default joint friction coefficient (N*m)
DEFAULT_JOINT_FRICTION: float = 0.0

# Default maximum joint effort (N*m)
DEFAULT_JOINT_EFFORT: float = 1000.0

# Default maximum joint velocity (rad/s)
DEFAULT_JOINT_VELOCITY: float = 10.0

# =============================================================================
# Angle Limits (radians)
# =============================================================================

# Full rotation range
FULL_ROTATION_RAD: float = 2.0 * math.pi

# Common joint limit presets
JOINT_LIMIT_SMALL: float = math.radians(30)  # ±30°
JOINT_LIMIT_MEDIUM: float = math.radians(60)  # ±60°
JOINT_LIMIT_LARGE: float = math.radians(90)  # ±90°
JOINT_LIMIT_FULL: float = math.pi  # ±180°

# =============================================================================
# Humanoid Proportions (from de Leva 1996)
# =============================================================================

# Total segments in standard humanoid model
HUMANOID_SEGMENT_COUNT: int = 22

# Default height for humanoid models (m)
DEFAULT_HEIGHT_M: float = 1.75

# Default mass for humanoid models (kg)
DEFAULT_MASS_KG: float = 75.0

# =============================================================================
# Mesh Processing
# =============================================================================

# Default mesh simplification ratio for collision geometry
COLLISION_MESH_SIMPLIFICATION: float = 0.3

# Minimum faces for simplified collision mesh
MIN_COLLISION_FACES: int = 50

# Maximum faces for detailed visual mesh
MAX_VISUAL_FACES: int = 10000

# =============================================================================
# Numerical Tolerances
# =============================================================================

# Tolerance for floating point comparisons
FLOAT_TOLERANCE: float = 1e-10

# Minimum mass to consider non-zero (kg)
MIN_MASS_KG: float = 1e-6

# Minimum inertia to consider non-zero (kg*m^2)
MIN_INERTIA_KG_M2: float = 1e-12

# =============================================================================
# URDF Generation
# =============================================================================

# Default URDF indent string
URDF_INDENT: str = "  "

# XML declaration for URDF files
URDF_XML_DECLARATION: str = '<?xml version="1.0"?>'

# Default robot name
DEFAULT_ROBOT_NAME: str = "humanoid"
