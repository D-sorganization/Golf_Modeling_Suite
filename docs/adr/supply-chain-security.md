# ADR: Supply-Chain Security via Action Pinning

## Status
Accepted

## Context
GitHub Actions are a supply-chain attack vector. Unpinned actions can silently upgrade to compromised versions.

## Decision
- Pin all GitHub Actions to commit SHAs
- Audit Python/Node/Rust dependencies weekly
- Use Dependabot for automated updates
- Require security review for new third-party tools

## Consequences
- Builds are deterministic and auditable
- Weekly maintenance burden for action updates
- But: Eliminates major attack surface

## Implementation
See `docs/ACTION_MANAGEMENT.md`
