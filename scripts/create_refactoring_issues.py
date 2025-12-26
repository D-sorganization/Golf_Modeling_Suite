#!/usr/bin/env python3
"""Create GitHub issues for code review refactoring initiative.

This script creates issues from templates in .github/ISSUE_TEMPLATE/
using the GitHub CLI (gh).

Usage:
    python scripts/create_refactoring_issues.py

Requirements:
    - GitHub CLI (gh) installed and authenticated
    - gh auth login (to authenticate)
"""

import subprocess
import sys
from pathlib import Path
import re


def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated."""
    try:
        subprocess.run(
            ["gh", "--version"],
            check=True,
            capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh) not found")
        print("Install: https://cli.github.com/")
        print()
        print("Alternative: Copy issue templates from .github/ISSUE_TEMPLATE/ manually")
        return False

    try:
        subprocess.run(
            ["gh", "auth", "status"],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        print("❌ Not authenticated with GitHub")
        print("Run: gh auth login")
        return False

    return True


def extract_issue_metadata(template_path):
    """Extract title and labels from template frontmatter."""
    content = template_path.read_text()

    # Extract title
    title_match = re.search(r"title:\s*['\"](.+?)['\"]", content)
    title = title_match.group(1) if title_match else template_path.stem

    # Extract labels
    labels_match = re.search(r"labels:\s*\[(.+?)\]", content)
    labels = []
    if labels_match:
        labels_str = labels_match.group(1)
        # Parse labels (handle quotes)
        labels = [
            l.strip().strip("'\"")
            for l in labels_str.split(",")
        ]

    # Extract body (skip YAML frontmatter)
    parts = content.split("---", 2)
    body = parts[2].strip() if len(parts) >= 3 else content

    return title, labels, body


def create_issue(template_path):
    """Create GitHub issue from template."""
    title, labels, body = extract_issue_metadata(template_path)

    print(f"Creating: {title[:60]}... ", end="", flush=True)

    # Build gh command
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]

    # Add labels
    for label in labels:
        cmd.extend(["--label", label])

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        # Extract issue number from URL
        issue_url = result.stdout.strip()
        issue_num = issue_url.split("/")[-1]

        print(f"✅ #{issue_num}")
        return issue_num

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed")
        print(f"  Error: {e.stderr}")
        return None


def main():
    """Main execution."""
    print("🚀 Creating Code Review Refactoring Issues")
    print("=" * 60)
    print()

    # Check prerequisites
    if not check_gh_cli():
        sys.exit(1)

    # Find all issue templates
    template_dir = Path(".github/ISSUE_TEMPLATE")
    if not template_dir.exists():
        print(f"❌ Template directory not found: {template_dir}")
        sys.exit(1)

    # Get templates in order
    templates = sorted(template_dir.glob("*.md"))
    if not templates:
        print(f"❌ No templates found in {template_dir}")
        sys.exit(1)

    print(f"Found {len(templates)} issue templates")
    print()

    # Create issues
    created_issues = {}

    for template in templates:
        issue_num = create_issue(template)
        if issue_num:
            created_issues[template.stem] = issue_num

    # Summary
    print()
    print("=" * 60)
    print("✅ Issue Creation Complete!")
    print("=" * 60)
    print()
    print("Created Issues:")
    for template_name, issue_num in created_issues.items():
        print(f"  #{issue_num} - {template_name}")

    if "00-refactoring-overview" in created_issues:
        master_issue = created_issues["00-refactoring-overview"]
        print()
        print(f"📋 Master Tracking Issue: #{master_issue}")

    print()
    print("Next steps:")
    print("1. Review created issues at: https://github.com/D-sorganization/Golf_Modeling_Suite/issues")
    print("2. Update master tracking issue with issue numbers")
    print("3. Assign issues to team members")
    print("4. Create project board for tracking progress")
    print()
    print("To create project board:")
    print("  gh project create --owner D-sorganization --title 'Code Review Refactoring'")


if __name__ == "__main__":
    main()
