# 3D_FullBody_Model: harden and isolate the scaffold branch before merge

## Context

PR #4386 adds a useful scaffold for `3D_FullBody_Model`, but it is not yet a
finished model and it currently overlaps with starting-pose matcher relocation
files. Before using it as the base for production full-body work, make the
branch internally consistent and easy to review.

## Target locations

- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/README.md`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/.gitignore`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/docs/LEG_CHAIN_DESIGN.md`
- `src/engines/Simscape_Multibody_Models/3D_FullBody_Model/matlab/scripts/`
- `SPEC.md`

## Required behavior

- Resolve the README vs `.gitignore` contradiction:
  - either generated `GolfSwing3D_FullBody.slx` is intentionally committed
  - or it remains generated-only and ignored
  - document the chosen policy explicitly
- State clearly that `add_leg_chain.m` is scaffold-only until the block creation
  phases are implemented.
- Add a build-report output location and format, even if MATLAB execution must
  be done by a user machine.
- Keep the scaffold PR focused. If possible, remove unrelated matcher relocation
  changes from the scaffold branch or rebase it after #4383 lands.
- Link PR #4386 to issue #4382 as "advances" rather than "closes" until full
  leg/contact validation is complete.

## Tests

- Existing MATLAB test harness should skip cleanly when generated `.slx` is
  absent and validate when present.
- Python/docs checks should pass.
- SPEC freshness should pass if source files change.

## Acceptance criteria

- Reviewers can merge the scaffold without believing it implements legs/contact.
- The generated-artifact policy is unambiguous.
- Branch overlap with #4383 is either eliminated or explicitly documented.

## Labels

`enhancement`, `matlab`, `documentation`, `hygiene`, `priority:high`
