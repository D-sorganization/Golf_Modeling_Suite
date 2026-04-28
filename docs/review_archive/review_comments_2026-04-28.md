# Review Comments Archive - 2026-04-28

Generated: 2026-04-28T07:53:09.237228

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3400: .github/workflows/Jules-PR-Cleanup.yml:94

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Restore compiled-PR branch matching in stale cleanup**

The new branch filter no longer matches `jules/compiled-*` branches, so stale compiled PRs are now skipped by cleanup even though `Jules-PR-Compiler.yml` still creates them (`compiled_branch = "jules/compiled-..."` at line 166). Before this change, `^jules/` covered those PRs; after this change they can accumulate indefinitely and never be auto-closed by...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3400#discussion_r3155070526)

---

### PR #3400: .github/workflows/Jules-Supersede-Check.yml:91

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Include compiled Jules branches in supersede scan**

This updated matcher also drops `jules/compiled-*`, so supersede detection will ignore compiled PRs even when a push to `main` overlaps most of their files. Since `Jules-PR-Compiler.yml` still emits `jules/compiled-...` branches (line 166), those PRs can remain open after being effectively replaced by merged changes, which defeats the purpose of the superse...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3400#discussion_r3155070531)

---

