# 3D_FullBody_Model: make logging prune measurable and reproducible

## Context

Issue #4382 estimates that the current 3D model has about 154 logged channels,
that 40-50% are redundant, and that pruning should reduce the surviving channel
set to about 115 while saving roughly 33-43 nonvirtual blocks. The scaffold
script `prune_redundant_logging.m` implements a conservative heuristic, but it
does not yet produce a measured before/after audit artifact.

## Target locations

- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/prune_redundant_logging.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/validate_3d_fullbody.m`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/docs/`
- `tests/` or MATLAB test harness under the full-body model directory

## Required behavior

Add a reproducible audit report with:

- source model path and hash/timestamp
- target model path
- before/after total block count
- before/after nonvirtual block estimate
- before/after logged signal count
- exact disabled block/outport paths
- category breakdown:
  - cosmetic/non-critical body logs
  - per-axis duplicate logs
  - local/global club duplicates
  - optional velocity/acceleration mirrors
- downstream signal requirements that were preserved

The report may be JSON, MAT struct, Markdown, or all three, but it must be
machine-readable enough for tests and human-readable enough for review.

## Important distinction

Do not report `round(0.7 * signals_disabled)` as measured savings. Keep
heuristic estimates separate from measured before/after block counts.

## Tests

- Dry-run mode returns a complete list of candidate changes without mutating the
  model.
- Audit report schema is stable and contains all required fields.
- Required downstream signals are checked against a documented allowlist.
- If MATLAB is unavailable in CI, add a static test for report parsing and a
  MATLAB-side test for real execution.

## Acceptance criteria

- A reviewer can answer: total signals before, redundant signals identified,
  exact signals removed, total signals after, measured block count after.
- The prune phase is safe to rerun and does not remove required optimizer,
  dataset, matcher, or force-analysis signals.
- Documentation explains whether pruning materially improves speed, clarity, or
  only block-budget headroom.

## Labels

`enhancement`, `matlab`, `performance`, `testing`, `motion`, `priority:high`
