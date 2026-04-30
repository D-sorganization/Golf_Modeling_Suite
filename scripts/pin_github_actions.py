#!/usr/bin/env python3
"""
Audit and pin all GitHub Actions to commit SHAs.
Run monthly to detect unpinned updates.
"""

import os
import re
import sys
from pathlib import Path

def parse_workflows(workflow_dir=".github/workflows"):
    """Find all GitHub workflow files."""
    return list(Path(workflow_dir).glob("**/*.yml"))

def extract_actions(workflow_content):
    """Extract all 'uses:' lines from a workflow."""
    lines = workflow_content.split('\n')
    actions = []
    for line in lines:
        if 'uses:' in line:
            # Skip local actions uses: ./.github/...
            if 'uses: ./' in line:
                continue
            # Extract: uses: owner/action@ref
            match = re.search(r'uses:\s*([^\s@]+)@([^\s]+)', line)
            if match:
                actions.append({
                    'full': f"{match.group(1)}@{match.group(2)}",
                    'owner_action': match.group(1),
                    'ref': match.group(2),
                    'line': line.strip(),
                })
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
    except Exception as e:
        print(f"ERROR resolving {owner_action}@{ref}: {e}", file=sys.stderr)
        return None

def main():
    workflows = parse_workflows()

    # We will only use PyGithub if we find unpinned actions
    github_api = None

    unpinned = []

    for workflow_file in workflows:
        content = workflow_file.read_text()
        actions = extract_actions(content)

        for action in actions:
            if len(action['ref']) == 40 or len(action['ref']) == 41:
                # Already pinned
                continue

            unpinned.append({
                'file': workflow_file,
                'action': action['owner_action'],
                'ref': action['ref'],
            })

    if unpinned:
        print(f"Found {len(unpinned)} unpinned actions:")

        token = os.getenv("GITHUB_TOKEN")
        if token:
            try:
                from github import Github  # pip install PyGithub
                github_api = Github(token)
            except ImportError:
                print("PyGithub is not installed. Please install it using `pip install PyGithub`.", file=sys.stderr)

        for u in unpinned:
            if github_api:
                sha = get_commit_sha(github_api, u['action'], u['ref'])
                if sha:
                    print(f"  {u['file']} : {u['action']}@{u['ref']} -> {sha}")
                    u['sha'] = sha
                else:
                    print(f"  {u['file']} : {u['action']}@{u['ref']} -> UNKNOWN")
            else:
                print(f"  {u['file']} : {u['action']}@{u['ref']}")

        if github_api and any('sha' in u for u in unpinned):
             print("\nTo pin, run:")
             for u in unpinned:
                 if 'sha' in u:
                     old = f"{u['action']}@{u['ref']}"
                     new = f"{u['action']}@{u['sha']}"
                     print(f"  sed -i 's/{old}/{new}/' {u['file']}")

        sys.exit(1)
    else:
        print("✓ All actions pinned to commit SHAs")
        sys.exit(0)

if __name__ == "__main__":
    main()
