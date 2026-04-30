# GitHub Actions Management Policy

## Overview

All GitHub Actions must be pinned to commit SHAs, not version tags, to prevent supply-chain attacks.

## Rationale

- **Version tags can move:** `actions/checkout@v4` can change if maintainer re-releases
- **Commit SHAs are immutable:** `actions/checkout@692973e3...` always refers to same code
- **Attack mitigation:** Pinning prevents silent upgrades to compromised versions

## Process

### When Adding a New Action

1. Find the action on GitHub: https://github.com/OWNER/ACTION
2. Get the full commit SHA for the release tag:
   ```bash
   git ls-remote https://github.com/actions/checkout refs/tags/v4
   # Output: 692973e3d937...  refs/tags/v4
   ```
3. Use in workflow:
   ```yaml
   uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332a  # v4.1.7
   ```
4. Add comment with version tag for human readability

### When Updating Actions

Run monthly:
```bash
cd .github
python ../scripts/pin_github_actions.py
git checkout -b chore/pin-actions
# Make changes
git commit -m "chore(ci): pin GitHub Actions to commit SHAs"
# Create PR
```

Dependabot will also create PRs for updates.

### Approval Process

- **Patch updates** (v4.0.0 → v4.0.1): Auto-merge (no breaking changes)
- **Minor updates** (v4.0.0 → v4.1.0): Code review required
- **Major updates** (v4.0.0 → v5.0.0): Architecture review + code review
- **New actions**: Security review (verify GitHub stars, maintenance status)

## Auditing

Check for unpinned actions:
```bash
grep -r "uses:" .github/workflows | grep -v "@[0-9a-f]\{40\}"
# Should return 0 results
```

## Related Links

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [npm audit advisory on unpinned SHAs](https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json)
- [SLSA Framework](https://slsa.dev/) — Supply-chain security levels
