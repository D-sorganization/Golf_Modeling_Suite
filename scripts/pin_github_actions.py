#!/usr/bin/env python3
"""
Audit and pin all GitHub Actions to commit SHAs.
Run monthly to detect unpinned updates.
"""

import os
import re
import sys
from pathlib import Path

from github import Github  # pip install PyGithub


def parse_workflows(workflow_dir=".github/workflows"):
    """Find all GitHub workflow files."""
    return list(Path(workflow_dir).glob("**/*.yml"))


def extract_actions(workflow_content):
    """Extract all 'uses:' lines from a workflow."""
    lines = workflow_content.split("\n")
    actions = []
    for line in lines:
        if "uses:" in line:
            # Extract: uses: owner/action@ref
            match = re.search(r"uses:\s*([^\s@]+)@([^\s]+)", line)
            if match and not match.group(1).startswith(".*"):
                actions.append(
                    {
                        "full": f"{match.group(1)}@{match.group(2)}",
                        "owner_action": match.group(1),
                        "ref": match.group(2),
                        "line": line.strip(),
                    }
                )
    return actions


def get_commit_sha(github_api, owner_action, ref):
    """
    Resolve a Git ref (tag/branch) to commit SHA.
    Example: actions/checkout@v4 → 692973e3d937129bcbf40652eb9f2f61becf3332a
    """
    try:
        repo = github_api.get_repo(owner_action)
        # Get the commit for this ref
        commit = repo.get_commit(ref)
        return commit.sha[:40]  # Full SHA
    except Exception as e:  # noqa: BLE001
        print(f"ERROR resolving {owner_action}@{ref}: {e}", file=sys.stderr)
        return None


def main():
    workflows = parse_workflows()

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        # Fallback for testing without token
        github_token = "dummy"
    github = Github(github_token)  # Requires auth
    unpinned = []

    for workflow_file in workflows:
        content = workflow_file.read_text()
        actions = extract_actions(content)

        for action in actions:
            if action["ref"].startswith("sha-") or len(action["ref"]) == 40:
                # Already pinned
                continue

            # Need to pin
            sha = get_commit_sha(github, action["owner_action"], action["ref"])
            if sha:
                unpinned.append(
                    {
                        "file": workflow_file,
                        "action": action["owner_action"],
                        "ref": action["ref"],
                        "sha": sha,
                    }
                )
            else:
                print(
                    f"ERROR: Could not resolve SHA for {action['owner_action']}@{action['ref']}",
                    file=sys.stderr,
                )
                sys.exit(1)

    if unpinned:
        print(f"Found {len(unpinned)} unpinned actions:")
        for u in unpinned:
            print(f"  {u['file']} : {u['action']}@{u['ref']} → {u['sha'][:8]}")

        # Generate patch script
        print("\nTo pin, run:")
        for u in unpinned:
            old = f"{u['action']}@{u['ref']}"
            new = f"{u['action']}@{u['sha']}"
            print(f"  sed -i 's/{old}/{new}/' {u['file']}")

        sys.exit(1)
    else:
        print("✓ All actions pinned to commit SHAs")
        sys.exit(0)


if __name__ == "__main__":
    main()
