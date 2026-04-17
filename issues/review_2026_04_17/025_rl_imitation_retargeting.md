# [HIGH] RL, imitation, and retargeting: non-determinism, broken IK, unsafe math, missing golf-domain rewards

## Summary

`src/learning/rl/`, `src/learning/imitation/`, and `src/learning/retargeting/`
have a number of concrete bugs and design gaps that compromise
reproducibility and correctness. Several of these are load-bearing
for any motion-capture-driven golf swing experiment.

## Findings (RL)

### 1. Double-negative action validation

`src/learning/rl/base_env.py:166-167`

```python
if not (action is not None):
```

Should be `if action is None`. This antipattern appears 325+ times
across the codebase — see issue #031.

### 2. Observation/action spaces built before `_get_n_joints()` subclass override

`src/learning/rl/base_env.py:99-100` — `spaces.Box(...)` is
instantiated in `BaseEnv.__init__` before subclass can override the
dimension. Subclasses that override dimensions do not update the
spaces.

### 3. Observation history multiplier is unused

`src/learning/rl/configs.py:93` — `get_obs_dim()` returns `n_joints *
history_length`, but `_get_observation()` never stacks history. Space
size and actual obs size drift silently.

### 4. Velocity reward is exponential of L2 error, saturates far from zero

`src/learning/rl/humanoid_envs.py:166`

```python
reward = np.exp(-np.linalg.norm(base_vel[:2] - target_vel[:2]))
```

At error = 1 m/s reward is 0.368; reward should be near zero at large
errors. Use `exp(−k·err²)` with tuned k, or a bounded `tanh` shaping.

### 5. Quaternion index assumptions

`src/learning/rl/humanoid_envs.py:216` — uses `quat[1], quat[2]`
assuming `[w, x, y, z]`; elsewhere in the codebase Pinocchio uses
`[x, y, z, w]`. Indexing must be explicit.

### 6. Base-env `close()` does not close the engine

`src/learning/rl/base_env.py:245` — resources leak over many episodes.

### 7. No golf-domain rewards

None of: clubhead-speed reward, swing-plane-deviation reward,
ball-flight reward, smash-factor reward. For a golf suite these are
the headline reward shapings; their absence means the RL stack has
no golf-specific signal to track.

## Findings (Imitation)

### 8. Unseeded permutations in training loop

`src/learning/imitation/learners.py:332` — `np.random.permutation`
without seeded RNG. Same dataset + config yields different
train/val splits across runs.

### 9. Discriminator "gradient" is just L2 regularization

`src/learning/imitation/learners.py:790-793` — the line marked as
discriminator update is only `layer.W -= lr · 0.01 · layer.W`.
This trains the discriminator toward zero, not toward discriminating.
GAIL is not actually running.

### 10. `.item()` on numpy arrays that may not be scalar

`src/learning/imitation/learners.py:857` — `.item()` raises for
non-scalar arrays; silent wrong-type return in branch.

### 11. Sigmoid has no clipping

`src/learning/imitation/learners.py:715-739` — `1 / (1 + exp(-x))`
overflows for large negative `x`. Clip `x` into `[-50, 50]` or use
`scipy.special.expit`.

### 12. `DAgger` actions array is off-by-one

`learners.py:540-565` — `demo_actions` has length `T`, while
`demo_positions`/`velocities` have `T + 1`. Zip with `strict=True`
raises.

## Findings (Retargeting)

### 13. Direct joint-angle copy ignores skeleton topology

`src/learning/retargeting/retargeter.py:366-372` — if source and
target skeletons differ in link lengths (arm length, torso length),
the copied joint angles produce an end-effector in the wrong place.
No IK pass to reconcile.

### 14. Inverse-kinematics only handles 2-joint chains

`retargeter.py:657-666` — law-of-cosines for 2 DOFs. Any 3+ DOF chain
has unmapped DOFs set to zero. Retargeting a mocap shoulder into a
3-DOF ball joint drops 2 DOFs of information.

### 15. Forward-kinematics assumes all joints rotate about Z

`retargeter.py:441-455` — `joint_axes` dict is defined but never
used; every joint is a Z-rotation. Humanoid shoulders and hips are
not Z-rotations.

### 16. Joint limits applied before optimization

`retargeter.py:367-372` — desired motion clipped before IK can
compensate; correct order is IK first, then limits.

## Findings (Sim2Real)

### 17. Gravity randomization range is ~1 %

`src/learning/sim2real/domain_randomization.py:55` — `(9.5, 10.1)`.
Earth gravity varies 0.3 % by latitude; this is a narrow window.
For sim-to-real robustness use `±5 %` minimum.

### 18. Mass randomization is silent if engine API is missing

`domain_randomization.py:160-164` — uses `hasattr(engine, "set_link_masses")`
and proceeds regardless. If the method is absent, the intended
randomization silently does nothing.

### 19. Action-delay buffer semantics broken at edges

`domain_randomization.py:270-275` — buffer indexing is not a proper
circular FIFO at the boundary.

### 20. Gravity sign assumes z-up

`domain_randomization.py:191-197` — sets `gravity[2] = -g_mag`. If
the engine is y-up, silently inverts gravity.

### 21. System-ID returns "converged" with an all-ones parameter on empty data

`src/learning/sim2real/system_identification.py:326` — `identify_from_trajectories([])`
returns `np.ones(n)` with `converged=True`. No error.

## Impact

Any "we trained a policy" or "we retargeted a PGA swing" claim made
with this stack has reproducibility and correctness problems.

## Acceptance Criteria

- [ ] Replace every `if not (x is not None)` with `if x is None` (see issue #031).
- [ ] Build spaces after subclass init; unit test space dims match obs dims.
- [ ] Actually stack observation history; test obs shape.
- [ ] Replace velocity reward with `exp(−k · ‖err‖²)` and document k.
- [ ] Adopt a single quaternion convention module-wide and assert the
      order in a fixture.
- [ ] Call `engine.close()` from `BaseEnv.close()`.
- [ ] Add a `GolfSwingEnv` with clubhead-speed reward, swing-plane
      deviation, smash-factor, ball-flight metrics.
- [ ] Use seeded `np.random.Generator` everywhere; deterministic
      train/val split.
- [ ] Replace the GAIL discriminator stub with an actual gradient.
- [ ] Guard `.item()` with `np.squeeze(...).item()` or return array.
- [ ] Clip sigmoid input or use `expit`.
- [ ] DAgger: align actions and states consistently.
- [ ] Retargeter: add IK after joint copy; use provided `joint_axes`;
      apply limits *after* IK.
- [ ] Broaden gravity range to ±5 %; require an explicit user opt-in
      for narrower randomization.
- [ ] `set_link_masses` must raise when the engine lacks support.
- [ ] Fix action-delay buffer edges; test with buffer-size-1.
- [ ] System-ID raises on empty trajectories.

## Related

- Issue #023 — realistic sensor noise is needed for sim-to-real.
- Issue #031 — repo-wide antipatterns including the double-negative.
