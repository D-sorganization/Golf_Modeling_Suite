# coordination: finish current matcher/full-body PRs and close superseded overlap cleanly

## Context

There are multiple active branches touching overlapping files. Before broad
implementation continues, clean up the queue so agents have one base for the
matcher and one base for the full-body model.

## Current state

- #4383 `feat/starting-pose-matcher` is the preferred matcher relocation PR.
- #4379 `feat/starting-pose-matcher-relocation` is older and appears
  superseded by #4383.
- #4386 `feat/3d-fullbody-scaffold` advances the full-body scaffold but also
  overlaps with matcher relocation files.
- #4376 should close through #4383.
- #4377 is updated by #4383 but is not currently formally linked.
- #4382 remains open until production full-body validation exists.

## Required behavior

1. Repair #4383 CI:
   - inspect exact current-head logs
   - fix Ruff findings
   - fix docs governance duplicate assessment placement
   - resolve Docker/Trivy `pin-pink` dependency issue or document if it is a
     repo-wide external blocker
2. After #4383 is green/merged:
   - close #4379 as superseded if no unique artifacts remain
   - link #4377 if #4383 truly satisfies it, or leave #4377 open with exact
     missing docs
3. Rebase or repair #4386:
   - remove duplicate matcher relocation changes if #4383 landed
   - keep #4386 focused on `3D_FullBody_Model`
   - state that it advances #4382 but does not close it
4. Keep all final implementation work on PRs.

## Tests

- Re-read live PR state before each merge/close decision.
- Use `gh pr diff --name-only` to confirm #4379 has no unique needed files
  before closing it.
- Do not claim merge completion until GitHub reports the merged state.

## Acceptance criteria

- One matcher relocation branch is merged.
- Superseded duplicate PR is closed with a clear comment.
- Full-body scaffold PR is focused and ready for follow-up implementation.
- Issues #4376, #4377, and #4382 reflect true remaining work.

## Labels

`enhancement`, `hygiene`, `ci`, `priority:high`
