# engines.physics_engines.mujocothon.mujoco_humanoid_golf.spatial_algebra.__init__

Spatial Algebra Module

This module implements Featherstone's spatial vector algebra for rigid body dynamics.
Spatial vectors are 6D vectors representing motion (velocity, acceleration) and
force (wrenches) in 3D space.

Key concepts:
- Spatial motion vectors: [angular_velocity; linear_velocity]
- Spatial force vectors: [moment; force]
- Spatial transformations (Plücker transforms)
- Spatial cross products
- Spatial inertia matrices

References:
    Featherstone, R. (2008). Rigid Body Dynamics Algorithms.
    Cambridge University Press.
