# Review Comments Archive - 2026-04-19

Generated: 2026-04-19T01:42:11.884060

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #2771: .github/test-mocking-violations.json:35

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Add the opensim violation to the JSON inventory**

The new `.github/test-mocking-violations.json` file closes the `violations` array after four entries, so it omits `tests/unit/engines/opensim/test_muscle_conditioning.py:37` even though this same commit lists that file as a flagged violation in the remediation doc. Any tooling or reporting that uses this JSON as the source of truth will miss an outstanding mo...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2771#discussion_r3105922879)

---

