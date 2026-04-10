# Platform Contract Hardening (April 2026)

- Status: active
- Evidence: active fix branches and 2026-04-10 commits for issues `#2447`, `#2448`, `#2449`, `#2450`, `#2451`, `#2452`, `#2453`, `#2466`, `#2469`, `#2473`, `#2475`, `#2479`, `#2481`, `#2487`, `#2489`, `#2492`, `#2493`, `#2495`, and `#2498`

## Problem Statement

UpstreamDrift is in a concentrated stabilization pass touching API routing, authentication defaults, launcher environment handling, simulator status reporting, registry paths, and engine-specific contracts. The work is substantial and cross-cutting, but the repository did not have a current workstream spec to keep those fixes aligned around one explicit intent.

## Scope

- Cover fixes that harden platform contracts instead of silently fabricating success or accepting inconsistent configuration.
- Cover API route registration, auth defaults, launcher environment/config behavior, simulator state reporting, and registry path correctness.
- Treat related engine-specific correctness fixes as part of the same stabilization campaign where they strengthen authoritative runtime behavior.

## Non-Goals

- A full rewrite of UpstreamDrift architecture.
- Product-roadmap feature work unrelated to the stabilization campaign.
- Treating docs-only cleanup or vendored-file removal as a standalone governed workstream.

## Architecture Or Design Notes

- Runtime surfaces should fail explicitly when dependencies, sockets, auth, or engine capabilities are invalid.
- Shared config and registry paths must resolve from authoritative repository layout instead of ad hoc relative assumptions.
- API route composition must stay canonical and avoid duplicated prefixes or shadow wiring.
- This is a bundled spec because the active fixes are converging on one goal: trustworthy platform boundaries.

## Acceptance Criteria

- API routes mount under the intended prefix exactly once.
- Auth-related defaults are safe by default and consistent across API surfaces.
- Launcher and registry configuration resolves from valid paths with test coverage.
- Simulator and engine integrations stop reporting false success when initialization or execution actually fails.
- Pull requests in this stabilization campaign reference this spec path.

## Validation Or Test Expectations

- Keep targeted unit tests for route prefixes, auth defaults, registry paths, launcher environment injection, terrain correctness, and simulator initialization behavior.
- Add focused regression tests whenever a fix changes an external contract.
- CI must pass without muting failures that the stabilization campaign is explicitly meant to surface.
