# ADR-0043: Companion Manifest Provider Authority

- Status: Accepted
- Date: 2026-08-28
- Decision Makers: UpstreamDrift maintainers and AffineDrift companion owners
- Related Issues/PRs: UpstreamDrift #9174, #9064, #9070; AffineDrift #4010

## Context

AffineDrift needs a complete, maintainable view of UpstreamDrift programs,
features, compatibility, support, workflows, documentation, and evidence. Today
the raw launcher manifest has 49 records, the repository-local model registry
has 56 records, and their union has 70 program identifiers. The feature-parity
registry has 41 records and 79 declared shell-source paths. These are migration
baselines, not stable product limits.

The default model discovery policy is intentionally useful for interactive
workstations: environment variables can add sibling/provider sources. That is
not safe for publication. An export could otherwise differ by machine, include
an unpinned sibling checkout, or silently change when a mutable external path
moves. Legacy launcher status also combines concepts such as maturity,
availability, support, parity, and readiness; collapsing those concepts would
overstate scientific or operational authority.

UpstreamDrift #9064 owns the governed design-manual program and #9070 defines a
typed calculation manifest. A companion catalog must not redefine equations,
methods, tolerances, uncertainty, or approval. It must expose software facts
that allow AffineDrift to link to those separate authorities.

## Decision

UpstreamDrift is the sole provider authority for the versioned
`upstreamdrift-companion` manifest. Version 1 uses the strict JSON Schema at
`docs/api/contracts/upstreamdrift-companion-v1.schema.json`. The deterministic
exporter writes ignored release artifacts to:

- `dist/companion/upstreamdrift-companion.v1.json`
- `dist/companion/upstreamdrift-companion.v1.json.sha256`

The JSON file is canonical UTF-8 with sorted keys, stable ID ordering, two-space
indentation, and one trailing newline. The digest covers those exact bytes.
Record counts remain an informational summary and migration-test expectation;
the schema does not use current counts as `const`, `minItems`, or `maxItems`.

### Source Ownership

| Fact                               | Editable Authority                        | Companion Treatment                                 |
| ---------------------------------- | ----------------------------------------- | --------------------------------------------------- |
| Native model and launch metadata   | `src/config/models.yaml`                  | Local-only normalized program record                |
| Web launcher metadata              | `src/config/launcher_manifest.json`       | Merged by stable program ID, with source provenance |
| Shell parity, gaps, and exemptions | `src/config/feature_parity.json`          | Feature record with parity kept separate            |
| Package and Python compatibility   | `pyproject.toml` plus supported CI matrix | Exact package version/specifier and tested minors   |
| Engine support tier                | UpstreamDrift support policy              | `supported`, `extended`, or `experimental` only     |
| Tools provider revision            | `vendor/ud-tools` Git gitlink             | Exact immutable 40-character commit                 |
| Equations/calculations/uncertainty | #9070 calculation manifest                | Link later; never copy or redefine                  |
| Design-manual content/approval     | #9064 governed QMD authority              | Link later; never infer approval                    |
| Scientific qualification           | Qualification evidence authority          | Conservative explicit state; inclusion grants none  |

The export keeps these independent dimensions:

1. `maturity`: lifecycle of the program implementation.
2. `availability`: whether the declared target can be reached and under what
   condition.
3. `support_tier`: maintenance/support promise for an engine.
4. `parity`: shell implementation relationship for a feature.
5. `scientific_qualification`: evidence-bounded validation status and scope.

Legacy statuses remain in `legacy_statuses` for auditability but are never the
authority for another dimension.

### Determinism and Authority Contracts

The exporter has the following preconditions:

- the source is a Git checkout at an exact 40-character commit;
- `GITHUB_SHA`, when present, equals the checked-out commit;
- an authoritative CLI export has no tracked or untracked changes other than
  ignored `dist/companion` outputs;
- every input is repository-relative, tracked at `HEAD`, and unchanged;
- model discovery is explicitly `local-only`, regardless of environment;
- `vendor/ud-tools` is a mode-`160000` gitlink at an exact commit.

The exporter hashes committed Git blob bytes rather than checkout bytes. This
makes provenance independent of CRLF/LF checkout policy. Wall-clock time,
sibling repositories, mutable absolute paths, provider-root environment
variables, initialized-submodule state, and installed engine runtimes are not
inputs.

Postconditions require unique, deterministically sorted program and feature
IDs, exact input hashes, exact provider pins, resolvable feature/program
references, a strict-schema-valid document, and a detached digest over the
rendered bytes. Publication remains `draft` while capability evidence,
workflow/document inventories, and screenshot qualification are incomplete.

### Provider and Consumer Boundary

UpstreamDrift produces and validates the manifest. AffineDrift consumes an
immutable release artifact pinned by repository, commit, schema version, and
SHA-256. AffineDrift may generate presentation components but must not repair,
augment, or reinterpret provider facts. A missing/unknown field, unsupported
schema version, digest mismatch, mutable URL, or unresolved reference fails
closed and requires an UpstreamDrift provider change.

The intended generated companion surfaces are:

- a compatibility/support overview;
- program catalog and program detail pages;
- feature parity/gap matrix;
- documentation and workflow cards;
- provenance/freshness panel; and
- qualified screenshot/evidence gallery.

Those views share one validated catalog adapter. Components receive typed view
models rather than reading JSON or constructing repository URLs independently
(Law of Demeter). Shared labels, URLs, versions, support badges, and status
mapping come from one adapter (DRY). The provider exporter does not import or
depend on AffineDrift.

## Alternatives Considered

1. Let AffineDrift scrape UpstreamDrift Markdown and source files. Rejected
   because source layout and prose are not a stable machine contract.
2. Export the default hybrid model registry. Rejected because results depend on
   environment variables and sibling checkout state.
3. Copy the calculation or manual schema into this manifest. Rejected because
   competing authorities would drift and could promote unqualified claims.
4. Treat the 49/56/70 and 41/79 baselines as schema invariants. Rejected because
   normal product growth would require a schema major version.
5. Commit a generated manifest containing its own source commit. Rejected
   because that creates a self-referential commit hash. The generated document
   and digest are protected build/release artifacts instead.

## Consequences

- Positive: one-way ownership, environment-independent output, immutable Tools
  provenance, conservative scientific semantics, and a small consumer API.
- Positive: TDD pins the migration baseline while allowing records to grow
  without schema churn; DbC rejects ambiguous publication inputs.
- Negative: a clean committed checkout is required to generate an authoritative
  artifact, so local drafts cannot be presented as publishable output.
- Negative: v1 initially publishes empty documentation, workflow, and screenshot
  inventories and remains explicitly blocked/draft until follow-up slices.

## Migration and Acceptance Gates

1. Add explicit `local-only` selection to `ModelRegistry` while preserving the
   legacy environment-controlled default for interactive callers.
2. Land the strict v1 schema, deterministic exporter, and RED-to-GREEN tests.
3. Prove the current 49 raw launcher, 56 local model, 70 union, 41 feature, and
   79 surface-path baseline only in tests and generated summary metadata.
4. Validate schema strictness, reference integrity, compatibility/support facts,
   clean-tree refusal, CI commit equality, immutable gitlink provenance, byte
   determinism, and detached digest generation.
5. In later provider PRs, add governed documentation/workflow records, engine
   capability evidence, screenshot capture/qualification, and protected CI
   artifact publication without changing calculation/manual authority.
6. AffineDrift #4010 pins a protected provider artifact and implements one
   validating adapter plus generated views. Consumer release remains blocked
   until digest, provenance, freshness, and qualification gates pass.

## Validation

Focused unit tests execute serially and explicitly perturb discovery/provider
environment variables. Ruff formatting/lint, mypy, title-case/document checks,
appropriate full tests, clean-tree CLI generation, detached SHA verification,
and protected non-draft review are required before release. Neither this ADR nor
a green structural test grants scientific or engineering approval.
