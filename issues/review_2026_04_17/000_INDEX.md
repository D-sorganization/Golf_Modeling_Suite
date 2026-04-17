# Comprehensive Repository Review — 2026-04-17

This directory holds the findings from a systematic, critical review of the
UpstreamDrift golf-swing humanoid modeling suite, produced on 2026-04-17.
Each file in this directory is a self-contained draft of a GitHub issue
and can be copied into a new issue verbatim (the directory structure is a
convenience; it does not have to be preserved on GitHub).

The review was structured across seven orthogonal axes executed as
independent deep-dives:

1. Physics engine wrappers (Drake / MuJoCo / Pinocchio / OpenSim / MyoSuite / Pendulum)
2. Robotics subsystem (whole-body control, contact, sensing, locomotion, planning)
3. Learning & research subsystems (RL envs, imitation, retargeting, sim2real, MPC, differentiable, multi-robot)
4. API server, launchers, and deployment
5. Test suite quality, coverage, and physics validation
6. Golf-domain modeling (aerodynamics, impact, shaft, humanoid, swing plane)
7. Cross-cutting concerns (logging, error handling, config, build, CI, docs, hygiene, typing, portability)

~370 concrete, file-and-line-referenced findings were identified across the
seven axes. They are grouped into the 21 GitHub issues listed below, each
of which bundles related findings to keep the tracker tractable.

## Issue Index

| #   | Title                                                                             | Severity |
| --- | --------------------------------------------------------------------------------- | -------- |
| 013 | Critical physics-convention bugs in engine wrappers (gravity, GRF, Jacobians)     | CRITICAL |
| 014 | Pinocchio integration order breaks energy conservation                            | HIGH     |
| 015 | Impact model: gear-effect sign error, angular-momentum non-conservation, loft ignored | CRITICAL |
| 016 | Aerodynamics model is not professionally calibrated (Cd / Cl / Magnus / wind)     | HIGH     |
| 017 | Humanoid URDF fidelity: toy-grade skeleton, asymmetric grip, missing joints       | HIGH     |
| 018 | Missing core golf-domain features (launch monitor, attack angle, spin loft, …)    | HIGH     |
| 019 | Shaft / club model gaps: no torsion, static loft, unused equipment specs          | HIGH     |
| 020 | Whole-body control: no damped pseudo-inverse, broken hierarchical QP, silent QP failures | CRITICAL |
| 021 | Contact & friction-cone model is non-conservative, ignores complementarity and impacts | HIGH     |
| 022 | ZMP / stability control is not valid during a golf swing (assumes walking gait)   | HIGH     |
| 023 | Sensor noise models are toy-grade (IMU, force-torque)                             | MEDIUM   |
| 024 | Motion planners have stubs, no smoothing, naive nearest-neighbor, no timeouts     | MEDIUM   |
| 025 | RL / imitation / retargeting: non-determinism, broken IK, math errors             | HIGH     |
| 026 | System-ID, domain randomization, MPC and differentiable physics correctness       | HIGH     |
| 027 | Test suite: mocked physics at module level, loose tolerances, tautologies         | CRITICAL |
| 028 | Missing critical physics validation tests (clubhead speed, impact, URDF mass, …)  | HIGH     |
| 029 | API security hardening: disabled auth defaults, CORS, path-traversal, CSRF        | CRITICAL |
| 030 | Launcher / process-manager races, UI thread blocking, unclean subprocess handling | HIGH     |
| 031 | Repo-wide code-quality antipatterns (`if not (x is not None)` x325, etc.)         | HIGH     |
| 032 | CI, docs, and hygiene bloat (56 workflows, committed artifacts, duplicate LICENSE) | MEDIUM   |
| 033 | Build / deploy hardening (Dockerfile pinning, Makefile/CLAUDE.md formatter mismatch) | MEDIUM   |

## Methodology

Findings were produced by running 7 parallel Explore-agent reviews with
narrow, expert prompts. Each agent returned file:line references,
severity, category, and a 1–3 sentence description. Findings were
manually reviewed and consolidated into the issues in this directory.
The review explicitly did **not** modify any source code; all output is
diagnosis-only. The `Tools` repository that UpstreamDrift vendors from
(`src/shared/python/upstream_drift_tools/`, etc.) was out of scope.

## How to turn these into GitHub issues

```
# Option 1 — create one issue per file with the `gh` CLI
for f in issues/review_2026_04_17/0[0-9][0-9]_*.md; do
  title=$(head -1 "$f" | sed 's/^# //')
  gh issue create --title "$title" --body-file "$f" --label review-2026-04-17
done

# Option 2 — copy-paste via the GitHub web UI
```

## Severity legend

- **CRITICAL** — correctness bug or security defect that violates core
  physics / security invariants; blocks claim of "professional-grade".
- **HIGH** — significant correctness/design gap; blocks a research-grade claim.
- **MEDIUM** — meaningful quality or robustness defect; should be on the roadmap.
- **LOW** — cleanup, portability, or stylistic concern.
