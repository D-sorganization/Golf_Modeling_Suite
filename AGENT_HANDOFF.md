# Agent Handoff — UpstreamDrift

Last updated: 2026-08-20

This is current operational state. Historical detail belongs in git/GitHub.

## Active Publication-Quality Slice (#8451)

Branch `feat/proximal-distal-publication-release` owns the PDF quality contract;
UpstreamDrift is authoritative, AffineDrift is its pinned publisher, and Tools/Sidekick only link.
The web-linearized 231-page candidate passes full-page inspection; archival release remains
blocked on missing tags, 110 Type 3 resources, and two unembedded resources. Phase 0 landed as
UpstreamDrift #8791, AffineDrift #3884, and Tools #4586; this branch is rebased on #8791 and
regenerates cleanly. CI Standard's `publication-quality` job now feeds the sole required gate.
After protected merge, advance the final revision and PDF/manifest digests through AffineDrift.
#8789 owns remaining Docker/quarantine/baseline work. This does not qualify
#8556, equipment calibration, or archival/PID release. Exact details are in
`docs/research/proximal_distal_energy_transfer/PUBLICATION_QUALITY.md`.

## Read This First — How Merging Works Now

Three workflows used to publish the required `quality-gate` status, so whichever
reported first satisfied branch protection and PRs merged while the real
aggregate was failing. #8747 fixed this and #8754 is closed. Consequences:

- The **only** required check is `quality-gate`, published solely by the
  aggregate job in `.github/workflows/ci-standard.yml`. The LoD gate publishes
  `lod-quality-gate`; docs CI publishes `docs-quality-gate`. **Never rename a
  job back to `quality-gate`** — that recreates the collision.
- If your run sits in `action_required`, wait: `approve-same-repo-runs.yml`
  approves same-repository runs every five minutes (fork PRs keep the manual
  gate). Do not disable it — branch updates come from a bot GitHub treats as a
  first-time contributor forever.
- `repo-structure-gates` runs its steps **sequentially and fail-fast**, so a red
  step hides every later one. Run the battery below first rather than spending
  a CI cycle per hidden failure. `check_architecture_budget.py` enforces a
  maximum of 100 lines per changed production Python function.

### Two Debt Ledgers — Remove-Only Ratchets

`scripts/config/unit_gate_quarantine.json` (520 node IDs, #8766) skips tests
that fail deterministically on main from the hollow-merge era, applied by
`_apply_unit_gate_quarantine` in `tests/conftest.py` only when
`UNIT_GATE_QUARANTINE=1` — which only the unit gate and `tests` job set.
`scripts/config/dry_duplication_quarantine.json` (#8763) tracks duplicate
fingerprints. **Entries may only be removed, never added**.
PR #8768 cleared main's ruff, bandit, XML security, and frontend lock debt.

### Traps That Cost Real Time

- **Committed evidence records hash-pin their sources.** Fourteen files under
  `tests/research/` are frozen by `source_sha256` maps in
  `docs/research/proximal_distal_energy_transfer/data/`. Never edit without
  updating the evidence manifest via `qualify_open_release write`.
- **Phantom Guard Scope Rules:** Conventional commit prefix for PR titles
  touching only `scripts/research/`, `docs/research/`, and `tests/research/`
  must use `test:`, `docs:`, or `chore:` rather than `feat:` (which requires
  diffs touching `src/`, `rust_core/`, or `api/`).

## Program Authority & Physics Epics State

- Epic #8557 governs the proximal-to-distal program; #8595 retains the agenda.
- #8789 is the Phase 0 truth-recovery gate for #8557. It keeps repository
  handoffs, GitHub issue states, release evidence, publication metadata, and CI
  from disagreeing.
- #8668 governs subject-scaled articulated contact; its qualification program
  remains open because #8751 and #8752 have unmet acceptance criteria.
- #8684 governs distributed grip, shaft, and ground:
  - #8751 is **OPEN**. PR #8783 added preliminary multi-station friction,
    power decomposition, and event probes, but stick/reversal controls,
    cross-engine active-set parity, registered horizon/refinement maps, and
    paper/release integration remain open.
  - #8752 is **OPEN**. PR #8783 added preliminary manufactured and Latin
    hypercube screens, but production-runner/two-engine manufactured cases,
    full shaft/ground parameter coverage, per-corner refinement, headline
    estimand movement, and uncertainty-adequacy evidence remain open.
- The release has 295 atomic claims and 40 reviewed release claims; all 40
  retain at least one scientifically open gate. #8724 still owns normalized
  four-way adjudication and independent review.
- Release-manifest validation on Windows exposed line-ending dependence plus
  genuinely stale hashes from post-release edits. #8789 owns the portable
  canonical-byte fix and manifest regeneration; do not report zero mismatches
  until `qualify_open_release validate` passes from a clean checkout.
- #8556 remains open: no governed participant dataset contains synchronized
  bilateral six-axis grip wrenches. Synthetic traces cannot replace it.

## Qualified Baseline — And Its Limits

Native MuJoCo and robotics Pinocchio independently qualify the 20-coordinate
rigid tree over 234 closed states, with power, passivity, energy, refinement,
geometry, and engine-parity controls. All of it is a synthetic structural
reference — not equipment calibration, anatomy, physiology, or coaching guidance.

- Of 384 coupled-versus-rigid shaft cells, 126 match on load and work; speed
  differences span `-0.0285` to `+0.0212 m/s` (82 negative), **rejecting a
  universal passive-shaft speed benefit**.
- The preregistered ground screen admits **0/384** coupled--fixed cells (ground
  damping asymmetry). A post-hoc screen admits 60 cells with mixed signs.
  **Do not read unmatched positive differences as a ground-pathway benefit.**
- Initialization: natural-zero, gravity-only, and conditional starts gave peak
  ground forces of 32.8, 565.5, and 510.3 N.

## Vendored Tools Dependency (`vendor/ud-tools`)

Tools is a **leaf dependency vendored as a submodule**. Never edit shared code
inside the vendored copy — Tools is the source of truth. The same rule binds
child copies under `src/shared/python/`.

- Tools #4577 & #4579 merged: Delivered PyQt6 Club Tester workbench, React panel
  (488 LOC), model interchange (MJCF/URDF/.osim), and sanitized auth logging
  resolving `UpstreamDrift#8770`.

## Immediate Next Steps

1. Publish #8451, then sync its exact revision and digests through AffineDrift.
2. Continue #8789's remaining Docker/quarantine/baseline work without overlap.
3. Complete #8751/#8752 and burn down #8766 without widening either contract.
4. Advance calibrated contact, full-delivery uncertainty, and #8556; begin the
   Sidekick epic only after those scientific and Tools boundaries are stable.

## Gate Commands

Run this locally before pushing; it mirrors the sequential CI steps:

```bash
python scripts/check_spec_paths.py && python scripts/check_root_clutter.py
python scripts/check_test_layout.py && python scripts/check_pytest_intree_testpaths.py
python scripts/ci/check_suite_marker_ratchet.py && python scripts/ci/check_dry_duplication_gate.py
python scripts/ci/check_architecture_budget.py
python scripts/check_module_size_budget.py --max-lines 1500 --include src
python scripts/check_doc_size_budget.py
python -m ruff check . && python -m ruff format --check .
```

Research validation:

```bash
python -m scripts.research.proximal_distal_energy.claim_audit validate
python -m scripts.research.proximal_distal_energy.claim_evidence_integrity validate
python -m scripts.research.proximal_distal_energy.momentum_question_readiness validate
python -m scripts.research.proximal_distal_energy.qualify_open_release validate \
  --source-revision "$(git rev-parse HEAD)" \
  --publication-profile computational
pytest tests/research -q
```

Do not infer human technique/physiology/injury/coaching; close #8556/#8557
without evidence; bypass protection; force-push/admin-merge; add ledger entries;
edit hash-pinned or Tools-owned files without regeneration; or rerun unchanged
capacity failures.
