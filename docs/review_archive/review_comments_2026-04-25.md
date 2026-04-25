# Review Comments Archive - 2026-04-25

Generated: 2026-04-25T10:54:07.240431

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #3276: src/shared/python/config/environment.py:553

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Keep GOLF_SUITE_MODE fallback in mode resolution**

This change drops support for the legacy `GOLF_SUITE_MODE` variable, so environments that have not migrated yet will silently fall back to the default mode (`remote`) and start enforcing auth where local-mode bypass previously worked. Because local auth behavior is security-critical and the repo still contains existing usage of the legacy names, this is a br...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3276#discussion_r3142346090)

---

### PR #3276: src/api/auth/security.py:28

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Accept legacy GOLF_API_SECRET_KEY during migration**

Reading only `UPSTREAM_API_SECRET_KEY` here breaks deployments that still provide `GOLF_API_SECRET_KEY`: in production, startup now raises a missing-secret runtime error; in non-production, the app falls back to a random per-process key and invalidates JWTs on restart. This should keep the legacy env var as a temporary fallback to avoid an outage during re...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3276#discussion_r3142346092)

---

### PR #3276: src/api/database.py:15

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Fallback to existing default SQLite file on rename**

Changing the implicit default database file name without a fallback/migration path causes users who rely on default `DATABASE_URL` behavior to boot against a brand-new empty SQLite database after upgrade, effectively hiding existing accounts and state stored in `golf_modeling_suite.db`. Add a compatibility check (or one-time migration) when the old file ex...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3276#discussion_r3142346095)

---

