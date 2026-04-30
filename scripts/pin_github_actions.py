#!/usr/bin/env python3
"""
Audit and pin all GitHub Actions to commit SHAs.
Run monthly to detect unpinned updates.
"""

import os
import re
import sys
from pathlib import Path

try:
    from github import Github  # pip install PyGithub
except ImportError:
    Github = None


def parse_workflows(workflow_dir=".github/workflows"):
    """Find all GitHub workflow files."""
    return list(Path(workflow_dir).glob("**/*.yml")) + list(
        Path(workflow_dir).glob("**/*.yaml")
    )


def extract_actions(workflow_content):
    """Extract all 'uses:' lines from a workflow."""
    lines = workflow_content.split("\n")
    actions = []
    for line in lines:
        if "uses:" in line:
            # We don't want to match local actions like uses: ./.github/workflows/...
            if "uses: ./" in line:
                continue
            # Extract: uses: owner/action@ref
            match = re.search(r"uses:\s*([^\s@]+)@([^\s]+)", line)
            if match:
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
    if not github_api:
        return None
    try:
        repo = github_api.get_repo(owner_action)
        # Get the commit for this ref
        commit = repo.get_commit(ref)
        return commit.sha[:40]  # Full SHA
    except Exception as e:  # noqa: BLE001
        print(f"ERROR resolving {owner_action}@{ref}: {e}", file=sys.stderr)
        return None


def main():  # noqa: C901
    workflows = parse_workflows()

    github = None
    if Github and os.getenv("GITHUB_TOKEN"):
        github = Github(os.getenv("GITHUB_TOKEN"))

    unpinned = []

    for workflow_file in workflows:
        try:
            content = workflow_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        actions = extract_actions(content)

        for action in actions:
            # if the ref contains 40 hex chars, we consider it pinned
            ref_clean = action["ref"].split("#")[0].strip()
            if re.match(r"^[0-9a-f]{40}$", ref_clean):
                # Already pinned
                continue

            # Need to pin
            sha = (
                get_commit_sha(github, action["owner_action"], ref_clean)
                if github
                else "0000000000000000000000000000000000000000"
            )
            if sha:
                unpinned.append(
                    {
                        "file": workflow_file,
                        "action": action["owner_action"],
                        "ref": ref_clean,
                        "sha": sha,
                    }
                )

    if unpinned:
        print(f"Found {len(unpinned)} unpinned actions:")
        for u in unpinned:
            print(f"  {u['file']} : {u['action']}@{u['ref']}")

        # We don't generate the script if we use dummy SHAs (no token)
        if github:
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
