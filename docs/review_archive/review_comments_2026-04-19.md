# Review Comments Archive - 2026-04-19

Generated: 2026-04-19T11:38:56.749699

## Reviewer (chatgpt-codex-connector[bot]) (4 comments)

### PR #2769: scripts/assess_repository.py:None

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Restore non-test repo coverage in secret scan**

Limiting the scan to `src/**/*.py`, `scripts/**/*.py`, and `examples/**/*.py` leaves other production Python files unscanned (for example root-level tooling and installer modules), so hardcoded credentials in those paths become false negatives. This regresses the previous `**/*.py` behavior and undermines the stated goal of repository-level secret detection out...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2769#discussion_r3105524301)

---

### PR #2769: .github/workflows/ci-standard.yml:None

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Capture Bandit output before failing the workflow step**

This command substitution runs under GitHub Actions' `bash -e` behavior, so a non-zero Bandit exit aborts the step at the assignment line before `exit_code=$?` and the summary `echo`s execute. When Bandit finds issues, the workflow therefore drops the intended diagnostic output/step summary, making remediation harder; wrap the Bandit call to allow capt...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2769#discussion_r3105524302)

---

### PR #2769: tests/unit/shared_python/test_assessment_analysis.py:51

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep bare-except fixture aligned with detection test**

`assess_error_handling_content` detects bare handlers via `except\s*:`; changing the fixture text to `except Exception as e:` means the fixture no longer contains the anti-pattern the test asserts. This makes `test_counts_bare_except` fail deterministically and breaks the validation of bare-except detection logic.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2769#discussion_r3105524303)

---

### PR #2769: src/shared/python/assessment/analysis.py:None

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Preserve grep_count exception contract or update callers**

Switching this precondition failure from `AssertionError` to `ValueError` changes externally observable behavior without synchronized caller/test updates; the existing unit contract still expects `AssertionError`, so the suite now fails on this path. If this is intentional, dependent tests/callers need to be updated in the same change to avoid a brok...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2769#discussion_r3105524305)

---

