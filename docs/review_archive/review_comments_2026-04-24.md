# Review Comments Archive - 2026-04-24

Generated: 2026-04-24T13:05:02.723602

## Reviewer (chatgpt-codex-connector[bot]) (3 comments)

### PR #3235: scripts/ci/check_pip_audit_waivers.py:147

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Serialize waiver dates before emitting JSON**

In `--json` mode this includes raw waiver entries from YAML (`"waivers": active`) and immediately calls `json.dumps`; with the current waiver file, `pyyaml` parses `expires_at` into `date` objects, which are not JSON serializable, so the script crashes with `TypeError` instead of returning JSON. This makes the advertised JSON integration path unusable for CI cons...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3235#discussion_r3140026820)

---

### PR #3235: scripts/ci/check_pip_audit_waivers.py:79

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P1 Badge](https://img.shields.io/badge/P1-orange?style=flat)</sub></sub>  Reject waivers missing expires_at**

A waiver entry without `expires_at` is only warned about and then added to `active`, which bypasses the expiry guard this script is meant to enforce. In practice, a typo or omitted field can create an indefinite security exception that still passes validation, so this should fail fast instead of being treated as valid.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3235#discussion_r3140026826)

---

### PR #3235: scripts/ci/check_pip_audit_waivers.py:95

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Treat date-only expiry as end-of-day**

The expiry check converts `YYYY-MM-DD` values to midnight UTC and expires waivers when `now >= expiry_date`, so a waiver listed as expiring on a given date is considered expired from the first second of that day. That causes CI to fail a full day earlier than the date most operators will expect from date-only metadata.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3235#discussion_r3140026830)

---

