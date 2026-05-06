# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T15:06:20.930074

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #4092: src/engines/CROSS_ENGINE_PARITY_SPEC.md:5

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Point the Simscape reference link to an existing spec file**

The opening paragraph links to `Simscape_Multibody_Models/3D_Golf_Model/PROJECT_SPEC.md`, but that file does not exist in the repository, so readers cannot reach the “production grade” reference this spec depends on. Because this document is meant to be the top-level contract for all engine work, a broken baseline reference makes the requirements a...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4092#discussion_r3197789997)

---

### PR #4092: src/engines/CROSS_ENGINE_PARITY_SPEC.md:58

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Replace nonexistent canonical loader path**

This section mandates using `shared/python/motion_matching/load_club_target.py`, but that module is not present, so contributors cannot comply with the “engine-specific loaders are forbidden” rule as written. As a result, implementers are forced to guess an alternative loader (or violate the spec), which undermines the parity contract this document is introducing.
...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4092#discussion_r3197789999)

---

### PR #4092: src/engines/CROSS_ENGINE_PARITY_SPEC.md:189

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Remove or defer links to missing per-engine spec docs**

The document says detailed implementation plans “live” in these four per-engine spec files, but none of the linked files currently exist. That leaves readers at dead links exactly where they expect actionable architecture details, which blocks the workflow this parity spec is trying to coordinate.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4092#discussion_r3197790006)

---

