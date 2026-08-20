# ADR 0035: Source-Backed Strokes-Gained Contract

## Status

Accepted

## Context

Launch-monitor applications need scoring analysis without confusing directional
dispersion with strokes gained. A defensible SG calculation requires complete
start and finish course state and a versioned expected-strokes benchmark.
Client-local implementations had weaker provenance and could hash equivalent
JSON numbers differently across Python and JavaScript.

## Decision

UpstreamDrift owns the canonical SG and outcome-proxy contracts.

- SG requires start and finish lie, context, target/hole, and distance.
- The baseline has a version, HTTP(S) source, license declaration, canonical
  SHA-256, and unique state/distance points.
- Canonical hashing normalizes finite numbers to 12 decimal places and sorts
  states, so row order and JSON number spelling do not affect identity.
- Interpolation is permitted only within an exact lie/context/target stratum;
  extrapolation fails closed with a structured exclusion.
- Results carry formula, units, row and dataset hashes, backing values,
  exclusions, uncertainty assumptions, and conservative claims.
- Grouped and longitudinal results require explicitly trusted identifiers,
  evidence, and a numeric order field. They remain descriptive.
- A separate outcome-proxy contract may report target-relative radial error,
  but its typed claims forbid describing that value as strokes gained.

## Consequences

React and PyQt clients can share one evidence-bearing scoring authority and
portable schema. Existing client-local baseline artifacts require an explicit
v2 migration. A source URL and license declaration are provenance fields, not
an independent legal or methodological endorsement. Baseline standard errors
are propagated when supplied; otherwise benchmark uncertainty is reported as
unavailable. No causal, device-emulation, or device-certification claim is
created.
