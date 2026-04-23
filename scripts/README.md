# Scripts

Last verified: 2026-04-23

This directory is the home for repository maintenance and CI helper scripts. Keep
new operational scripts here instead of adding Python entrypoints at the repo root.

## Directory guide

- `scripts/chore/`: one-off repository maintenance helpers that may rewrite files.
- `scripts/maintenance/`: durable operational metadata or maintenance helpers that
  support CI and release workflows.
- `scripts/`: CI gates and frequently used helpers that are still in the flat
  layout pending broader cleanup.

## Focused inventory

| Script | When to run | Entry point |
| --- | --- | --- |
| `check_no_print_calls.py` | In CI to block new `print()` calls in production code touched by a branch. | `python scripts/check_no_print_calls.py` |
| `check_root_level_scripts.py` | In CI to block net-new repo-root Python scripts unless explicitly allowlisted. | `python scripts/check_root_level_scripts.py` |
| `chore/patch_analyzers.py` | When shared perturbation analyzer base helpers change and engine analyzer classes need the patch applied in place. | `python scripts/chore/patch_analyzers.py` |
| `chore/replace_prints.py` | During supervised cleanup work to replace legacy `print()` calls in `src/` with `logger.info()` scaffolding. Review the diff before committing. | `python scripts/chore/replace_prints.py` |
| `maintenance/ci_trigger.py` | When a maintainer needs the tracked CI trigger token value referenced by operational docs or workflow debugging. | `python scripts/maintenance/ci_trigger.py` |
