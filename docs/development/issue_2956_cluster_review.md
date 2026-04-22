# Issue #2956 Cluster Review

**Date:** 2026-04-22
**Scope:** Repeated filename clusters reported for `__main__`, `analyzer`, `base`, `code_quality_check`, and `codeIssuesGUI`

## Review Summary

This review checked the repeated filename clusters reported by the assessment scan and split them into two buckets:

1. Intentional entrypoints or abstract bases that are repeated by design.
2. A genuine code-copy cluster that should stay synchronized.

## Findings

| Cluster | Status | Review outcome |
| --- | --- | --- |
| `__main__` | Justified | These files are package entrypoints. Each one launches the local module or engine it sits beside, so the shared name is conventional rather than duplicate implementation. |
| `analyzer` | Justified | These are engine-specific analyzer implementations with different runtime dependencies and behavior. The shared logic already lives in `src/shared/python/perturbation/analyzer_base.py` and related helpers. |
| `base` | Justified | These are abstract base modules for unrelated subsystems. The repeated basename is a common layout pattern, not duplicated behavior. |
| `code_quality_check` | Consolidated | `src/tools/code_quality_check.py` is the authoritative implementation. The engine-local copies are thin wrappers that forward to the shared script. |
| `codeIssuesGUI` | Justified for now | The four MATLAB files are byte-identical launchers kept next to their respective toolboxes. They should be treated as synchronized entrypoints unless the repo later introduces a shared MATLAB helper layer. |

## Notes

- No broad behavior change was needed for the `__main__`, `analyzer`, or `base` clusters.
- The `code_quality_check` cluster is already deduplicated by delegation.
- The MATLAB `codeIssuesGUI.m` copies are the only remaining exact-copy cluster in this review; they are preserved to keep each toolbox self-contained on the MATLAB path.

## Follow-up Protection

- A regression test now checks that the `code_quality_check.py` wrappers still delegate to the shared implementation.
- The same test also verifies the MATLAB `codeIssuesGUI.m` copies remain byte-identical so drift is visible immediately.
