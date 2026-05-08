# 3D FullBody Logging Prune Audit

`matlab/scripts/prune_redundant_logging.m` emits a reproducible audit report
for logging-prune runs on the 3D fullbody Simscape model. The report has two
audiences:

- JSON for CI, reviewers, and later regression comparisons.
- Markdown for humans reviewing block-budget and signal-budget headroom.

The schema version is `3d_fullbody_logging_prune_audit.v1`.

## Report Contract

Required top-level fields:

- `schema_version`
- `generated_at`
- `model_name`
- `dry_run`
- `aggressive`
- `source_model`
- `target_model`
- `measured_counts`
- `heuristic_estimates`
- `signals_disabled`
- `disabled_block_paths`
- `disabled_outport_paths`
- `candidates`
- `category_breakdown`
- `downstream_signal_requirements`
- `artifacts`
- `notes`

`source_model` and `target_model` include `path`, `exists`, `timestamp`, and
`sha256`. `measured_counts.before` and `measured_counts.after` each include
`total_blocks`, `nonvirtual_blocks`, and `logged_signal_count`; each count is a
`value` plus a `measured` flag.

`heuristic_estimates` is intentionally separate. The legacy
`round(0.7 * disabled_signal_count)` calculation is an estimate, not a measured
block delta, and must not be used as the measured before/after block count.

## Candidate Categories

- `cosmetic_non_critical_body_logs`: visual, marker, and cosmetic body logging.
- `per_axis_duplicate_logs`: X/Y/Z channels derivable from preserved vector
  channels.
- `local_global_club_duplicates`: local club force/torque/angular channels when
  global-frame channels remain preserved.
- `optional_velocity_acceleration_mirrors`: aggressive-mode mirrors that can be
  derived from position plus `dt`.

Every candidate records `category`, `kind`, `path`, `property`, `action`, and
`mutated`. A dry run sets `mutated=false` for every candidate.

## Downstream Signal Policy

The audit preserves required downstream channels through
`downstream_signal_requirements.allowlist`. Reviewers should treat that allowlist
as the signal contract for optimization, matcher, force analysis, and bus
extraction code. A prune run may disable derivable duplicates, but it must not
disable the documented downstream analysis channels.

## Reproducible Usage

```matlab
load_system("FullBodyGolfSwing3D")
opts = struct( ...
    "dry_run", true, ...
    "json_report_path", "reports/fullbody_logging_prune_audit.json", ...
    "markdown_report_path", "reports/fullbody_logging_prune_audit.md");
report = prune_redundant_logging("FullBodyGolfSwing3D", opts);
```

Set `dry_run=false` only after reviewing the candidate list. The same report
schema is returned in both modes so before/after signal counts, exact disabled
paths, measured block counts, category breakdowns, and heuristic estimates remain
comparable across runs.
