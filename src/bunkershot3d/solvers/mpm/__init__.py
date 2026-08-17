"""The F1 tier: a 2-D plane-strain material-point sand solver (ADR-0033).

F0 (:mod:`bunkershot3d.solvers.drft`) integrates an empirical resistive
stress over the intruder's swept surface.  It never forms a sand
velocity, at any resolution, so no amount of post-processing yields the
*fields* Track B of epic #8699 consumes.  A continuum solve produces them
by construction: every cell carries a velocity, a density and a stress
because those are the solution variables.

What this package is
--------------------

* :mod:`.constitutive` -- rate-independent **Drucker-Prager**
  elastoplasticity with a compressive cap read off the sand's own packing
  state, and the reason ``mu(I)`` was rejected (it is ill-posed at both
  low and high inertial number, so refinement makes it worse).
* :mod:`.grid` -- the Eulerian background grid, quadratic B-splines and
  the **APIC** transfers, which conserve linear *and* angular momentum
  where PIC damps and FLIP rings.
* :mod:`.body` -- the clubhead as a rigid moving plane-strain section,
  with the contact treatment that stops material tunnelling through it.
* :mod:`.solver` -- :class:`~bunkershot3d.solvers.mpm.solver.PlaneStrainMPMSolver`,
  which implements the :class:`~bunkershot3d.solvers.protocol.GranularSolver`
  protocol so F1 is swappable with F0.
* :mod:`.envelope` -- the F1 validity verdict, its caveats, and the
  quantities ADR-0033 refuses outright.
* :mod:`.verification` -- conservation residuals, the analytic cases, the
  grid-convergence study and the F0 cross-check.

What it is not
--------------

Plane strain has **no out-of-plane flow**: sand moving heel-to-toe along
the face does not exist in this model, and no refinement adds it.  F1 is
specified at bulk resolution (``dx ~ 1-2 mm``) for the 10-100 mm flow
features, so the ~0.5 mm leading edge is deliberately under-resolved and
**club force remains F0's to report**.  Validation for this package
stands at NASA-STD-7009B level 0 of 4; nothing here is a physical
prediction.
"""

from __future__ import annotations

from .constitutive import (
    HARDIN_RICHART_ANGULAR_COEFFICIENT_KPA,
    HARDIN_RICHART_ROUND_COEFFICIENT_KPA,
    PLANE_STRAIN_DIMENSION,
    SAND_POISSON_RATIO,
    SandContinuum,
    drucker_prager_alpha,
    hencky_kirchhoff_principal,
    principal_stretches,
    project_to_yield_surface,
    reconstruct,
    yield_function,
)

__all__ = [
    "HARDIN_RICHART_ANGULAR_COEFFICIENT_KPA",
    "HARDIN_RICHART_ROUND_COEFFICIENT_KPA",
    "PLANE_STRAIN_DIMENSION",
    "SAND_POISSON_RATIO",
    "SandContinuum",
    "drucker_prager_alpha",
    "hencky_kirchhoff_principal",
    "principal_stretches",
    "project_to_yield_surface",
    "reconstruct",
    "yield_function",
]
