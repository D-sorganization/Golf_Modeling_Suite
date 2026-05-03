#!/usr/bin/env python3
"""Fail if the repository root contains files outside the allowlist."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWLIST = frozenset(
    {
        ".dockerignore",
        ".env.docker.example",
        ".env.example",
        ".gitattributes",
        ".gitignore",
        ".gitmodules",
        ".pre-commit-config.yaml",
        "AGENTS.md",
        "CHANGELOG.md",
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "Cargo.toml",
        "Dockerfile",
        "Dockerfile.heavy_test",
        "LICENSE",
        "Makefile",
        "README.md",
        "SECURITY.md",
        "SPEC.md",
        "alembic.ini",
        "build_hooks.py",
        "conftest.py",
        "docker-compose.gpu.yml",
        "docker-compose.yml",
        "environment.yml",
        "install.sh",
        "launch_golf_suite.py",
        "package-lock.json",
        "package.json",
        "pyproject.toml",
        "requirements-dev.lock",
        "requirements.lock",
        "rust-toolchain.toml",
    }
)
IGNORED_WORKTREE_FILES = frozenset({".git"})


def find_disallowed_root_files(repo_root: Path) -> list[Path]:
    """Return root files that are not approved for repository-level storage.

    Preconditions:
        repo_root exists and points to a directory.

    Postconditions:
        Returned paths are relative to repo_root and sorted by name.
    """
    if not repo_root.exists():
        raise FileNotFoundError(f"repo root does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise NotADirectoryError(f"repo root is not a directory: {repo_root}")

    violations: list[Path] = []
    for entry in repo_root.iterdir():
        if entry.is_dir() or entry.name in IGNORED_WORKTREE_FILES:
            continue
        if entry.name not in ALLOWLIST:
            violations.append(Path(entry.name))

    return sorted(violations, key=lambda path: path.as_posix())


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser for the root clutter guard."""
    parser = argparse.ArgumentParser(
        description="Fail if unapproved files are present at the repository root."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root to inspect.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the repository-root clutter guard."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        violations = find_disallowed_root_files(args.repo_root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        logger.error("FAIL: %s", exc)
        return 1

    if violations:
        logger.error("FAIL: disallowed files at repo root:")
        for violation in violations:
            logger.error("  %s", violation.as_posix())
        logger.error("Move or delete them. ALLOWLIST changes require PR review.")
        return 1

    logger.info("OK: No disallowed files found at repo root.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
