# Review Comments Archive - 2026-05-06

Generated: 2026-05-06T14:54:59.762977

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #4087: .github/workflows/docs-currency-warning.yml:69

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Prevent advisory job from failing on read-only PR tokens**

This workflow is documented as advisory-only, but `gh pr comment` runs under `set -e` and will exit non-zero when the `pull_request` event provides a read-only `GITHUB_TOKEN` (common for forked and Dependabot PRs). In those contexts the step fails instead of degrading gracefully, so the check can become a failing status even though it is intended to ...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4087#discussion_r3197730238)

---

### PR #4087: .github/workflows/docs-currency-warning.yml:48

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Restrict docs-match pattern to the three canonical docs**

The docs-currency policy says motion-matching PRs should update one of the three canonical docs, but this matcher treats any `*_SPEC.md`/`*_GUIDE.md`/`*_PLAYBOOK.md` anywhere in the repo as satisfying the requirement. A PR can therefore bypass the intended warning by touching an unrelated spec/guide/playbook file, producing false negatives in the advi...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/4087#discussion_r3197730241)

---

