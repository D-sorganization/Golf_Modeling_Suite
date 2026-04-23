#!/usr/bin/env python3
"""Block net-new repository-root Python scripts outside the allowlist."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_ALLOWLIST = frozenset(
    {
        "build_hooks.py",
        "conftest.py",
        "launch_golf_suite.py",
        "setup_golf_suite.py",
        "start_api_server.py",
    }
)


def _run_git(args: list[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def changed_paths(repo_root: Path, base_ref: str) -> list[str]:
    output = _run_git(["diff", "--name-only", "--diff-filter=AR", f"{base_ref}...HEAD"], repo_root)
    return [line.strip() for line in output.splitlines() if line.strip()]


def find_disallowed_root_python_files(
    changed_file_paths: list[str], allowlisted: set[str]
) -> list[str]:
    violations: list[str] = []
    for raw_path in changed_file_paths:
        path = Path(raw_path)
        if len(path.parts) != 1:
            continue
        if path.suffix != ".py":
            continue
        if path.name in allowlisted:
            continue
        violations.append(path.as_posix())
    return sorted(violations)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Block net-new repository-root Python files unless allowlisted."
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref used for diff (default: origin/main).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    repo_root = Path(__file__).resolve().parent.parent

    try:
        paths = changed_paths(repo_root, args.base_ref)
    except RuntimeError as exc:
        if args.base_ref == "HEAD~1":
            logger.error("FAIL: Unable to compute changed files: %s", exc)
            return 1
        paths = changed_paths(repo_root, "HEAD~1")

    violations = find_disallowed_root_python_files(paths, set(DEFAULT_ALLOWLIST))
    if violations:
        logger.error("FAIL: Net-new root-level Python files require an allowlist review:")
        for violation in violations:
            logger.error("  %s", violation)
        logger.error("\nMove maintenance helpers under scripts/ or update the allowlist intentionally.")
        return 1

    logger.info("OK: No disallowed net-new root-level Python files detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
