# [MEDIUM] Motion planners have stubs, no smoothing, O(n) nearest-neighbour, no valid timeouts

## Summary

`src/robotics/planning/` provides RRT(-star) + collision checking as
the motion-planning subsystem. Several missing methods, naive
algorithms, and incomplete broad-phase checks make it unsuitable for
live humanoid-golf use.

## Findings

### 1. `_steer()` is called but not defined in visible code

`src/robotics/planning/motion/rrt.py:177`

If the base class doesn't provide `_steer`, the planner silently falls
back to whatever the default is (likely returning `q_rand` verbatim),
i.e., no actual steering. Effective step size is unbounded, kinematic
feasibility is not enforced.

### 2. `_aabb_overlap()` is called but not defined

`src/robotics/planning/collision/collision_checker.py:281`

The broad-phase call simply returns `False`, meaning every collision
query hits the narrow phase. On complex humanoid+club models this is
O(n²) per query — unusable for RRT in real time.

### 3. Nearest-neighbour is brute-force O(n)

`src/robotics/planning/motion/rrt.py:262-282` — loop over every tree
node. Use `scipy.spatial.cKDTree` (rebuild every k insertions) or
`sklearn.neighbors.BallTree` for configuration-space distance.

### 4. Distance metric is unweighted Euclidean

RRT distance uses `np.linalg.norm(q1 − q2)`. For a humanoid with
pelvis translation in metres and wrist rotation in radians these
have different scales; the planner biases toward whichever dimension
is largest. Use a weighted metric with weights from joint-range or
end-effector-Jacobian-based metric.

### 5. No post-path smoothing (shortcutting)

`rrt.py:243-260` returns raw waypoints. Golf-swing trajectory planning
with jerky waypoints causes actuator saturation. Add a shortcut-
based smoother and a temporal B-spline fit.

### 6. Path extraction order is wrong

`src/robotics/planning/motion/rrt.py:284-300` — path is built from
goal backward, never reversed. Clients expecting `path[0] == q_start`
will get `path[0] == q_goal`.

### 7. No planner timeout / progress feedback

Planners return FAILURE on exceeding max iterations but do not
emit any progress telemetry. Impossible to debug "why is the plan
taking forever" without log instrumentation.

### 8. Goal tolerance is single-number

`planner_base.py` uses a scalar goal tolerance. Golf end-effector
placement needs component-wise tolerances (position vs. orientation
vs. velocity).

### 9. Tree nodes store full configuration copies

`rrt.py:49-51, 130` — every node holds `np.ndarray` copy. Memory
grows linearly with tree size. Use an index into a shared array.

## Impact

Motion planning cannot be used live. For pre-computed swing
trajectories, output is jerky and not time-parameterised.

## Acceptance Criteria

- [ ] Implement `_steer(q_near, q_rand, max_step)` with kinematic
      bounds; unit test on a simple 2-link arm.
- [ ] Implement `_aabb_overlap()` broad phase; profile before/after on
      a humanoid model.
- [ ] Replace linear nearest-neighbour with cKDTree; rebuild every
      `k` insertions. Benchmark.
- [ ] Swap to weighted or Jacobian-based distance metric.
- [ ] Add shortcut smoother + time-parametrized B-spline output.
- [ ] Reverse the extracted path so `path[0] == q_start`.
- [ ] Add timeout + per-iteration progress callback.
- [ ] Support component-wise goal tolerance (dict of joint-name → tol,
      or a cartesian SE(3) tolerance for EE tasks).
- [ ] Node struct holds `int` index instead of a copy; contiguous
      config array.

## Related

- Issue #020 — WBC path-tracking depends on these paths.
- Issue #018 — golf-swing trajectory generation pipeline.
