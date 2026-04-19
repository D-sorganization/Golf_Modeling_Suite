# Review Comments Archive - 2026-04-16

Generated: 2026-04-16T21:26:06.302646

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #2720: .pre-commit-config.yaml:44

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Use cross-platform interpreter for formatter hook**

The new `formatter-guidance-consistency` hook invokes `python3` via `language: system`, which will fail on setups that only provide `python` on PATH (a common Windows configuration). Since this hook is marked `always_run: true`, those contributors will be blocked from committing any change, not just formatter-related edits. Please make the hook interpreter-...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2720#discussion_r3097772501)

---

### PR #2721: src/api/local_server.py:214

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Narrow drive-path check to avoid breaking valid SPA URLs**

The new `":" in normalized` guard rejects any path segment containing a colon, and `serve_spa` now converts that `ValueError` into HTTP 400. This regresses valid client-side routes such as timestamp or namespaced IDs (for example, `/timeline/2026-04-17T10:30:00Z`) that previously fell back to `index.html` and let the SPA router handle them. The valid...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/2721#discussion_r3097816287)

---
