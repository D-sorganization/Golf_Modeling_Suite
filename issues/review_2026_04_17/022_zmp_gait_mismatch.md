# [HIGH] ZMP / gait stack is a walking-humanoid library bolted onto a stationary swing

## Summary

`src/robotics/locomotion/` implements a bipedal walking gait stack
(ZMP, footstep planner, gait state machine). A golf swing is a
*stationary* sequence: feet do not move. The current code assumes
feet are in motion, quasi-static CoM acceleration is zero, and
support polygons are default rectangles. None of these assumptions
hold during a swing, so the library neither validates stability nor
contributes to control during the actual use case.

## Findings

### 1. CoM acceleration hard-coded to zero

`src/robotics/locomotion/zmp_computer.py:295-304`

```python
def _estimate_com_acceleration(self):
    return np.zeros(3)
```

The exact ZMP formula requires `a_com` and is
`x_zmp = x_com − (z_com − z_zmp) · a_com,x / (a_com,z + g)`. With
`a_com = 0` this degenerates to "CoM projected on ground", which is
valid only when the humanoid is not accelerating. During a downswing
the CoM accelerates rapidly (`|a| > 5 m/s²`); ZMP is then off by many
centimetres and any stability check using it is wrong.

### 2. Support polygon defaults to a 30×45 cm rectangle

`src/robotics/locomotion/zmp_computer.py:332-342`

No API passes the actual feet polygon. A golfer's stance varies
significantly between clubs (driver is wide, wedge is narrow);
hard-coded foot geometry means stability margins are meaningless.

### 3. No double-support transition logic

`src/robotics/locomotion/zmp_computer.py:126-196` — ZMP is computed
as a single-contact or two-contact formula without a weighting
parameter for load distribution. A swing is fundamentally in
asymmetric double support: ~65 % of weight on the trail foot at the
top, shifting to ~80 % on the lead foot at follow-through. Without
load distribution, ZMP is not physically defined.

### 4. Capture point is computed with the single-support formula

`src/robotics/locomotion/zmp_computer.py:198-234`

Always uses `ICP = CoM + v/ω`. During double support the capture
point is not defined without a reference foot; current code returns
a garbage vector.

### 5. Gait state machine is time-driven, not event-driven

`src/robotics/locomotion/gait_state_machine.py:226-246`

Phase transitions fire on timers. Feet-planted events are not
checked. Irrelevant for a swing (no gait phases), but if the
scheduler runs at all it will spuriously "advance" through walking
phases the humanoid is not executing.

### 6. Footstep planner does not validate kinematic reach

`src/robotics/locomotion/footstep_planner.py:252-312` — planner
generates steps with no IK reachability check. Downstream IK fails
and the error does not carry the planner's step data for diagnosis.

### 7. Yaw extraction from quaternion lacks gimbal-lock handling

`src/robotics/locomotion/footstep_planner.py:62-67`

Custom 2-arg atan2 formula with no singularity guard; at near-pure
pitch/roll the yaw is undefined and the planner places feet with
random orientations.

### 8. Missing: stance-width optimizer / address-position composer

There is no module that takes a `ClubSpec` + `TargetShot` and returns
a stance width, ball position, and shoulder alignment. Everything
currently starts from a pre-authored keyframe.

## Impact

Claims like "we can evaluate balance during the downswing" are not
supported by the current code. Perturbation analyses that report a
"stability score" are using a broken ZMP metric.

## Acceptance Criteria

- [ ] Implement a proper `a_com` estimator using `Ẍ` filtered from the
      WBC stack (or central-difference on CoM trajectory).
- [ ] Allow a dynamic support polygon from the actual foot-frame
      poses; add a test of golfer-specific stance widths.
- [ ] Extend ZMP to weighted-double-support with an explicit load-
      distribution input.
- [ ] Gate the capture-point API to single-support only; return `None`
      with a log message in double support.
- [ ] Replace time-driven gait FSM with an event-driven one; skip the
      FSM entirely when running a `SwingStance` scenario (see issue #020).
- [ ] Reachability-check steps before emitting; raise a
      `FootstepUnreachableError`.
- [ ] Use a robust yaw extractor (`scipy.spatial.transform.Rotation.as_euler`)
      and guard near-gimbal-lock cases.
- [ ] Add a new module `src/robotics/locomotion/golf_stance.py` that
      composes a static stance from `ClubSpec` + `TargetShot`.

## Related

- Issue #020 — whole-body control needs a static-stance gait plugin.
- Issue #018 — missing golf-domain features; this issue is a prerequisite
  for a swing-fault detector that flags sway/slide.
