# ARCHITECTURE_DEBT:
# This module historically exceeds standard length metrics and accumulates excessive domain responsibility.
# It requires domain-aware structural extraction to isolate its internal classes appropriately.

"""Green Surface Model for Putting Simulation.

This module defines the putting green surface including slopes,
undulations, elevation contours, and hole position.

Supports loading topographical data from various formats:
- NumPy arrays (heightmaps)
- CSV files
- GeoTIFF (if rasterio available)
- JSON contour definitions

Design by Contract:
    - All positions are in meters
    - Elevations are relative to a reference plane
    - Slopes are expressed as gradients (rise/run)
"""

from __future__ import annotations

=======
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

>>>>>>> origin/main
import numpy as np

from src.engines.physics_engines.putting_green.python._surface_analysis import (
    SurfaceAnalysisMixin,
)
from src.engines.physics_engines.putting_green.python._surface_data import (
    ContourPoint,
    SlopeRegion,
)
from src.engines.physics_engines.putting_green.python._surface_geometry import (
    SurfaceGeometryMixin,
)
from src.engines.physics_engines.putting_green.python._surface_io import (
    SurfaceIOMixin,
)
from src.engines.physics_engines.putting_green.python._surface_presets import (
    SurfacePresetsMixin,
)
from src.engines.physics_engines.putting_green.python.turf_properties import (
    TurfProperties,
)

__all__ = [
    "ContourPoint",
    "GreenSurface",
    "SlopeRegion",
]


<<<<<<< HEAD
class GreenSurface(
    SurfaceGeometryMixin,
    SurfaceAnalysisMixin,
    SurfaceIOMixin,
    SurfacePresetsMixin,
):
    """Putting green surface model with elevation and slope data.

    Supports multiple ways to define the surface:
    1. Flat surface (default)
    2. Slope regions (circular areas with uniform slope)
    3. Contour points (scattered elevation samples, interpolated)
    4. Heightmap (2D array of elevations)

    Attributes:
        width: Width of green [m]
        height: Height of green [m]
        turf: Turf properties
        hole_position: Position of hole [m, m]
        hole_radius: Radius of hole [m] (standard = 0.054m = 4.25"/2)
    """

    STANDARD_HOLE_RADIUS = 0.054  # 4.25 inches diameter / 2

    def __init__(
        self,
        width: float = 20.0,
        height: float = 20.0,
        turf: TurfProperties | None = None,
    ) -> None:
        """Initialize green surface.

        Args:
            width: Width of putting surface [m]
            height: Height of putting surface [m]
            turf: Turf properties (defaults to standard)
        """
        if not (width is not None):
            raise ValueError("width must be provided")
        if not (width is not None):
            raise ValueError("width must be provided")
        self.width = width
        self.height = height
        self.turf = turf or TurfProperties()

        self._init_geometry()

        # Hole
        self._hole_position = np.array([width / 2, height / 2])
        self.hole_radius = self.STANDARD_HOLE_RADIUS

    @property
    def hole_position(self) -> np.ndarray:
        """Get hole position."""
        return self._hole_position

    def set_hole_position(self, position: np.ndarray) -> None:
        """Set hole position."""
        self._hole_position = np.array(position[:2])

=======
    def add_slope_region(self, region: SlopeRegion) -> None:
        """Add a slope region to the green."""
        self._slope_regions.append(region)

    def set_contour_points(self, points: list[ContourPoint]) -> None:
        """Set elevation from scattered contour points.

        Points are interpolated to create a smooth surface.

        Args:
            points: List of ContourPoint objects
        """
        if points is None:
            raise ValueError("points must be provided")
        self._contour_points = points
        self._build_contour_interpolator()

    def _build_contour_interpolator(self) -> None:
        """Build interpolator from contour points."""
        if not self._contour_points:
            return

        x = np.array([p.x for p in self._contour_points])
        y = np.array([p.y for p in self._contour_points])
        z = np.array([p.elevation for p in self._contour_points])

        # Use RBF interpolation for smooth surface
        try:
            self._heightmap_interpolator = interpolate.RBFInterpolator(
                np.column_stack([x, y]),
                z,
                kernel="thin_plate_spline",
                smoothing=0.01,
            )
        except (ValueError, TypeError, RuntimeError):
            # Fallback to linear interpolation
            self._heightmap_interpolator = interpolate.LinearNDInterpolator(
                np.column_stack([x, y]), z, fill_value=0.0
            )

    def set_heightmap(
        self,
        heightmap: np.ndarray,
        smooth: bool = True,
        smooth_sigma: float = 1.0,
    ) -> None:
        """Set surface from 2D heightmap array.

        Args:
            heightmap: 2D array of elevation values [m]
            smooth: Whether to smooth the heightmap
            smooth_sigma: Gaussian smoothing sigma
        """
        if heightmap is None:
            raise ValueError("heightmap must be provided")
        if smooth:
            heightmap = ndimage.gaussian_filter(heightmap, sigma=smooth_sigma)

        self._heightmap = heightmap.astype(np.float64)

        # Build interpolator
        ny, nx = heightmap.shape
        x = np.linspace(0, self.width, nx)
        y = np.linspace(0, self.height, ny)

        self._heightmap_interpolator = interpolate.RegularGridInterpolator(
            (y, x),
            self._heightmap,
            method="cubic",
            bounds_error=False,
            fill_value=0.0,
        )

    def get_elevation_at(self, position: np.ndarray) -> float:
        """Get elevation at a position.

        Args:
            position: [x, y] position on green [m]

        Returns:
            Elevation at position [m]
        """
        if position is None:
            raise ValueError("position must be provided")
        pos = np.clip(position[:2], [0, 0], [self.width, self.height])

        # Base elevation from heightmap or contours
        elevation = 0.0

        if self._heightmap_interpolator is not None:
            if self._heightmap is not None:
                # Regular grid interpolator (y, x order)
                elevation = float(self._heightmap_interpolator([[pos[1], pos[0]]])[0])
            else:
                # RBF interpolator (x, y order)
                elevation = float(self._heightmap_interpolator([[pos[0], pos[1]]])[0])

        # Add ridge contributions
        for ridge in self._ridges:
            elevation += self._ridge_elevation(pos, ridge)

        # Add depression contributions
        for depression in self._depressions:
            elevation += self._depression_elevation(pos, depression)

        return elevation

    def get_gradient_at(self, position: np.ndarray, delta: float = 0.01) -> np.ndarray:
        """Get elevation gradient at position.

        Uses numerical differentiation.

        Args:
            position: [x, y] position on green [m]
            delta: Step size for numerical gradient [m]

        Returns:
            [dz/dx, dz/dy] gradient vector
        """
        if position is None:
            raise ValueError("position must be provided")
        pos = position[:2]

        # Central difference
        dzdx = (
            self.get_elevation_at(pos + [delta, 0])
            - self.get_elevation_at(pos - [delta, 0])
        ) / (2 * delta)

        dzdy = (
            self.get_elevation_at(pos + [0, delta])
            - self.get_elevation_at(pos - [0, delta])
        ) / (2 * delta)

        return np.array([dzdx, dzdy])

    def get_slope_at(self, position: np.ndarray) -> np.ndarray:
        """Get slope vector at position.

        Combines contributions from slope regions and elevation gradient.

        Args:
            position: [x, y] position on green [m]

        Returns:
            [slope_x, slope_y] slope vector (gradient)
        """
        if position is None:
            raise ValueError("position must be provided")
        pos = position[:2]
        total_slope = np.zeros(2)

        # Contribution from slope regions
        for region in self._slope_regions:
            weight = region.get_weight(pos)
            if weight > 0:
                total_slope += weight * region.slope_magnitude * region.slope_direction

        # Contribution from elevation gradient
        if self._heightmap_interpolator is not None:
            gradient = self.get_gradient_at(pos)
            total_slope += gradient

        return total_slope

    def get_gravitational_acceleration(self, position: np.ndarray) -> np.ndarray:
        """Get gravitational acceleration component on sloped surface.

        On a slope, gravity has a component parallel to the surface
        that accelerates the ball downhill.

        Args:
            position: [x, y] position on green [m]

        Returns:
            [ax, ay] gravitational acceleration [m/s²]
        """
        if position is None:
            raise ValueError("position must be provided")
        slope = self.get_slope_at(position)
        # Acceleration is proportional to slope and points downhill
        # a = g * sin(theta) ≈ g * slope for small slopes
        return -GRAVITY_M_S2 * slope

>>>>>>> origin/main
    def is_in_hole(
        self, position: np.ndarray, velocity: np.ndarray | None = None
    ) -> bool:
        """Check if ball position is in the hole.

        A ball is considered holed if:
        1. It's within the hole radius
        2. If moving, velocity is low enough to not lip out

        Args:
            position: Ball position [m, m]
            velocity: Ball velocity [m/s] (optional, for lip-out check)

        Returns:
            True if ball is holed
        """
<<<<<<< HEAD
        if not (position is not None):
            raise ValueError("position must be provided")
        if not (position is not None):
            raise ValueError("position must be provided")
        distance = np.linalg.norm(position[:2] - self._hole_position)

        if distance > self.hole_radius:
            return False

        # Check for lip-out at high speeds
        if velocity is not None:
            speed = math.hypot(*velocity)
            # Empirical: ball lips out if going too fast near edge
            max_speed_at_edge = 1.5  # m/s
            if distance > self.hole_radius * 0.5 and speed > max_speed_at_edge:
                return False

        return True

    def is_on_green(self, position: np.ndarray) -> bool:
        """Check if position is on the green surface."""
        if not (position is not None):
            raise ValueError("position must be provided")
        if not (position is not None):
            raise ValueError("position must be provided")
        x, y = position[:2]
        return 0 <= x <= self.width and 0 <= y <= self.height
