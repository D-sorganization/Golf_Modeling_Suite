# Security Policy

This document describes the vulnerability disclosure process, SBOM artifact management,
OSV monitoring cadence, and waiver renewal procedures for UpstreamDrift.

---

## Vulnerability Disclosure

### How to Report

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities by emailing the maintainers at the address listed in
[SECURITY.md](../../SECURITY.md) at the repository root, or by using GitHub's
private vulnerability reporting feature:
<https://github.com/D-sorganization/UpstreamDrift/security/advisories/new>

Include:

- A description of the vulnerability and affected component(s).
- Steps to reproduce or a proof-of-concept (if available).
- The version(s) of UpstreamDrift affected.
- Any suggested mitigations you are aware of.

### Response SLA

| Severity (CVSS v3) | Initial acknowledgement | Triage complete | Fix or mitigation target |
|--------------------|------------------------|-----------------|--------------------------|
| Critical (9.0–10)  | 1 business day         | 3 business days | 7 calendar days          |
| High (7.0–8.9)     | 2 business days        | 5 business days | 30 calendar days         |
| Medium (4.0–6.9)   | 5 business days        | 10 business days| 90 calendar days         |
| Low (0.1–3.9)      | 10 business days       | 30 business days| Next scheduled release   |

If a fix cannot be shipped within the target window (e.g., no upstream patch exists),
a waiver is created in `scripts/config/pip_audit_waivers.json` with an expiry date
and a linked GitHub issue. See [Waiver Renewal](#waiver-renewal) below.

---

## SBOM Artifacts

### Format

SBOMs are generated in **CycloneDX 1.4 JSON** format using `cyclonedx-bom>=4.0.0`.

### Generation Workflow

The workflow `.github/workflows/sbom.yml` runs automatically on every `release`
event (when a GitHub Release is published) and can also be triggered manually via
`workflow_dispatch`.

Three artifacts are produced per release, one per supported tier:

| Artifact name        | Extras installed              | Output file                  |
|----------------------|-------------------------------|------------------------------|
| `sbom-core`          | (none — base install only)    | `sbom-core.cdx.json`         |
| `sbom-extended`      | `drake`, `pinocchio`          | `sbom-extended.cdx.json`     |
| `sbom-experimental`  | `opensim`, `myosuite`         | `sbom-experimental.cdx.json` |

Artifacts are retained for **90 days** on GitHub Actions and are also attached to
the corresponding GitHub Release page.

### Consuming SBOMs

Download artifacts from the Actions run or the Release page, then inspect with any
CycloneDX-compatible tool:

```bash
# Example: list all components in the core SBOM
python3 -c "
import json, sys
data = json.load(open('sbom-core.cdx.json'))
for c in data.get('components', []):
    print(c['name'], c.get('version', ''))
"
```

---

## Supported Tiers and Security Coverage

| Tier         | pip extras              | OSV scan | SBOM | pip-audit |
|--------------|-------------------------|----------|------|-----------|
| core         | (none)                  | yes      | yes  | yes       |
| extended     | `drake`, `pinocchio`    | yes      | yes  | yes       |
| experimental | `opensim`, `myosuite`   | yes      | yes  | best-effort |

The **experimental** tier contains optional biomechanics engines whose upstream
packages may lag on vulnerability fixes. Waivers for experimental-tier CVEs have
a shorter default expiry (60 days) to encourage regular re-evaluation.

---

## OSV Monitoring Cadence

The workflow `.github/workflows/osv-scan.yml` runs `google/osv-scanner` against
the project lock files on the following schedule:

- **Daily at 06:00 UTC** (automated schedule).
- **On demand** via `workflow_dispatch`.

The scan covers:

- `requirements.lock` — production dependency snapshot.
- `requirements-dev.lock` — development/test dependency snapshot.

If the scanner reports any unfixed vulnerabilities, the workflow fails and appears
as a failing CI check, alerting the team. Findings are listed in the job summary.

To investigate a failing scan locally:

```bash
# Install the OSV scanner CLI
# https://google.github.io/osv-scanner/installation/

osv-scanner --lockfile=requirements.lock --lockfile=requirements-dev.lock
```

---

## Waiver Renewal

Active waivers live in `scripts/config/pip_audit_waivers.json`. Each waiver entry
has the form:

```json
{
  "vuln_id": "CVE-YYYY-NNNNN",
  "reason": "Human-readable justification",
  "expires": "YYYY-MM-DD",
  "ticket": "https://github.com/D-sorganization/UpstreamDrift/issues/NNNN"
}
```

### Renewal Procedure

1. **Check upstream status.** Verify whether a fix version now exists for the
   affected package (`pip index versions <package>` or the OSV advisory page).

2. **If a fix is available:** Upgrade the package, remove the waiver entry, and
   open a PR referencing the original ticket.

3. **If no fix is available:** Extend the `expires` date by at most 90 days,
   update the `reason` field with the latest upstream status, and reference or
   update the linked issue.

4. **CI enforcement:** The pip-audit CI step reads `pip_audit_waivers.json` and
   fails if any waiver has an `expires` date in the past. Expired waivers must be
   renewed or the vulnerability resolved before the branch can merge.

5. **Waiver PRs** must be reviewed by at least one maintainer and should tag the
   original security ticket for traceability.
