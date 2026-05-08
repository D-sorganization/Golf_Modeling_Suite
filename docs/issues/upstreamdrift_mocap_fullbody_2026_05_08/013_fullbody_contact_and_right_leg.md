# 3D_FullBody_Model: mirror second leg and add foot-ground contact forces

## Context

After one leg is scripted and stable, mirror the second leg and add ground
contact. This should be a separate issue because contact stiffness, damping,
friction, and pelvis anchoring can destabilize the model.

## Target locations

- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/add_leg_chain.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/validate_3d_fullbody.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/docs/LEG_CHAIN_DESIGN.md`

## Required behavior

- Mirror the implemented leg to the opposite side with consistent naming:
  `LHip/RHip`, `LKnee/RKnee`, `LAnkle/RAnkle`.
- Add ground plane at z=0.
- Add one Spatial Contact Force per foot, sphere/plane geometry.
- Use model-workspace contact parameters:
  - `GroundContactStiffness`
  - `GroundContactDamping`
  - `GroundFrictionStatic`
  - `GroundFrictionKinetic`
- Add a short static/address-pose validation run.
- Decide and document pelvis anchoring behavior:
  - existing translation joint remains initial pelvis placement
  - ground reaction forces close the loop through the legs
  - any temporary settle/weld behavior must be explicitly named and removable

## Tests

- MATLAB smoke sim with both legs and contact for at least 0.005 s.
- Longer sim target once contact is stable.
- Validation report includes contact blocks and both foot sensors.
- Static address pose vertical ground reaction force is sanity-checked against
  body weight within a documented tolerance if signal access permits.

## Acceptance criteria

- Both legs and foot-ground contacts are present in the generated model.
- The model remains below the 1000 nonvirtual block budget with documented
  headroom.
- Contact parameters are configurable without editing block internals.

## Labels

`enhancement`, `matlab`, `physics`, `motion`, `testing`, `priority:high`
