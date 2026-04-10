# Specification Workflow

Active workstream specs live in `docs/specs/active/`. Planned work that is not yet approved belongs in `docs/specs/planned/`. Implemented specs that still govern current behavior can live in `docs/specs/implemented/`. Superseded material moves to `docs/archive/specs/`.

Use a spec for architecture changes, new features, API or schema changes, workflow changes, and multi-file refactors. Do not require a spec for typo fixes, dependency bumps, or isolated non-behavioral cleanup.

Every active spec must include:

- problem statement
- scope
- non-goals
- architecture or design notes
- acceptance criteria
- validation or test expectations
- current status (`proposed`, `active`, `implemented`, `superseded`, or `archived`)

Implementation branches, pull requests, and issue threads for substantial work must reference the governing spec path. If a legacy root `SPEC.md` exists, treat it as the umbrella repository spec until the relevant workstreams are split into `docs/specs/`.

## Index

- Active: `docs/specs/active/`
- Planned: `docs/specs/planned/`
- Implemented: `docs/specs/implemented/`
- Archived: `docs/archive/specs/`

Create the smallest possible spec that keeps intent, scope, and validation current with the codebase.
