# [HIGH] Contact, friction-cone, and impact handling is inadequate for club/ball/ground physics

## Summary

The contact subsystem (`src/robotics/contact/`) is a steady-state
single-point-contact model. It cannot represent the defining contact
events of a golf swing: (a) club–ball impact (impulsive), (b) club–
ground (turf) scuffing, and (c) ball–surface rolling/spinning after
landing. The friction cone linearization is non-conservative, there is
no complementarity enforcement, and the grasp matrix assumes point
contact with force-only coupling.

## Findings

### 1. Friction cone pyramid is inscribed, not circumscribed

`src/robotics/contact/friction_cone.py:172-212`

The pyramid edges `d − μ·n` inscribe the true cone, which *under-
constrains* tangential force: the solver can allocate `‖f_t‖ > μ·f_n`
along directions between pyramid edges. For a club–ball impact this
can permit an unphysical sliding force. Standard practice: use an
outer (circumscribed) pyramid for conservative constraints or use a
second-order cone program (SOCP) to enforce the exact cone.

### 2. No complementarity enforcement

`src/robotics/contact/friction_cone.py:273-315`

`project_to_friction_cone` projects onto the surface but does not
enforce `f_n · (separating acceleration) = 0`. The result can report
positive normal force while the contact is actually separating,
producing phantom support.

### 3. Grasp matrix assumes point contact with force-only coupling

`src/robotics/contact/grasp_analysis.py:19-72`

`G = [I; r×]` omits torsional friction and rolling resistance. For a
ball-on-turf contact patch (~1 cm²), the rolling-resistance torque is
what stops a putt from rolling forever. Missing.

### 4. Only the linear block of the contact Jacobian is used

`src/robotics/contact/contact_manager.py:256-269`

If `J.shape == (6,n)`, code takes rows 0:3 and drops rotational
coupling. Club head rotates at ~70 rad/s at impact; rotational
coupling is not negligible.

### 5. No impact (impulsive) dynamics path

Throughout the contact subsystem there is no branch for `dt = 0`
impulsive contact — the model is set up for steady/quasi-static
contact. `tests/acceptance/` has no impact-restitution test on the
WBC stack.

### 6. Convex-hull support-polygon fallback silences scipy failures

`src/robotics/contact/contact_manager.py:354-367`

When `scipy.spatial.ConvexHull` raises, code silently falls back to a
Graham-scan implementation. Any user investigating "why is the
support polygon wrong" will have no signal that the fast path is
degenerate.

### 7. Contact force non-negativity silently clipped

`src/robotics/contact/contact_manager.py:190`: `normal_force = max(0, ...)`.
For real contacts this is correct, but when the *input* is negative
(indicating the contact model has been exited), silently clipping to
zero hides a regression in the upstream dynamics.

### 8. No turf / tee / bunker surface model

There is no module that represents a soft (sand, rough, fairway,
green) surface. Ball landing physics (`src/engines/physics_engines/putting_green/`)
uses constant friction on a hard floor.

## Impact

Club–ball impact, divots, and ball landing are all core golf
phenomena that cannot be simulated in the current architecture.

## Acceptance Criteria

- [ ] Switch friction cone to a circumscribed pyramid or SOCP; add a
      worst-case tangential-direction test.
- [ ] Add explicit complementarity residual check
      `‖f_n ⊙ a_sep‖ < 1e-6` in the QP post-solve; expose the residual.
- [ ] Use the full 6-row contact Jacobian; test rolling-resistance on a
      spinning ball.
- [ ] Add an impulsive-contact path: given pre-impact velocities and a
      coefficient-of-restitution contact model, compute post-impact
      velocities in a single solver call. Wire this to the impact model
      in issue #015.
- [ ] Surface a warning when the scipy convex-hull fast path falls
      back to Graham scan.
- [ ] Raise on negative normal-force inputs instead of silently clipping.
- [ ] Add a turf model (Mazer–Fowler or similar) with parameters for
      fairway / rough / bunker / green; wire to landing physics.

## Related

- Issue #015 — impact model.
- Issue #020 — whole-body controller contact-constraint Jacobian.
- Issue #022 — stationary stance during a swing.
