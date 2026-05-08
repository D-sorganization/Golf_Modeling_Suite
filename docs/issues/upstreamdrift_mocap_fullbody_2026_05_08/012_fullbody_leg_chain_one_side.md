# 3D_FullBody_Model: implement one scripted leg chain before mirroring

## Context

`add_leg_chain.m` currently declares the intended hip/knee/ankle/foot design
but does not call `add_block`, `set_param`, or `add_line` for real Simscape
construction. Implement one side first to reduce wiring risk.

## Target locations

- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/add_leg_chain.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/docs/LEG_CHAIN_DESIGN.md`
- Existing joint libraries:
  - `src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/model/Kinetically_Driven_Gimbal_Joint.slx`
  - `src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/model/Kinetically_Driven_Revolute_Joint.slx`
  - `src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab/src/model/Kinetically_Driven_Universal_Joint.slx`

## Required behavior

Implement the left or right leg only:

- hip gimbal joint with X/Y/Z position and torque inputs
- upper-leg rigid body
- knee revolute joint
- lower-leg rigid body
- ankle universal joint
- foot rigid body
- ball-of-foot contact sphere frame, even if contact force is added later
- transform sensors needed for downstream logs
- minimal signal routing to the existing combined bus

The script must be reproducible: delete/rebuild behavior or idempotent checks
must be defined so re-running `build_3d_fullbody` does not duplicate blocks.

## Tests

- MATLAB load/build smoke test with `opts.skip_contact=true`.
- Validation report shows block delta for the one-leg phase.
- Required start-position variables are present in model workspace.
- Required polynomial coefficient names are discoverable or explicitly reported
  as pending if coefficients are added in a later issue.

## Acceptance criteria

- One leg is actually present in the generated model, not just documented.
- Generated model stays below the 1000 nonvirtual block budget.
- The build script can be rerun from a clean checkout.

## Labels

`enhancement`, `matlab`, `physics`, `motion`, `TDD`, `priority:high`
