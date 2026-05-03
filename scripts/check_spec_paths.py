"""Validate repository-relative paths documented in SPEC.md.

The checker intentionally scopes itself to architecture-owned SPEC sections so
examples and user-facing command snippets are not treated as filesystem
contracts.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

SPEC_PATH_PATTERN = re.compile(r"`([^`]+)`")
VALIDATED_SECTION_HEADINGS = (
    "### Key Components",
    "### Component Path Ownership",
)
REPO_PATH_PREFIXES = (
    ".github/",
    "docs/",
    "rust_core/",
    "scripts/",
    "shared/",
    "src/",
    "tests/",
    "ui/",
)
ROOT_VALIDATED_PATHS = {"SPEC.md"}


class SpecPath(NamedTuple):
    """Repository-relative path documented in a validated SPEC section."""

    value: str


class SpecPathViolation(NamedTuple):
    """Path validation failure found in SPEC.md."""

    value: str
    reason: str

    def __str__(self) -> str:
        return f"{self.value}: {self.reason}"


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")


def _require_path(value: Path, name: str) -> None:
    if not isinstance(value, Path):
        raise TypeError(f"{name} must be a pathlib.Path")


def _section_body(spec_text: str, heading: str) -> str:
    _require_text(spec_text, "spec_text")
    _require_text(heading, "heading")

    lines = spec_text.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("#"):
            break
        if in_section:
            collected.append(line)
    return "\n".join(collected)


def _is_repo_path(value: str) -> bool:
    return (
        (value in ROOT_VALIDATED_PATHS or value.startswith(REPO_PATH_PREFIXES))
        and "\\" not in value
        and ".." not in value
    )


def extract_spec_paths(spec_text: str) -> list[SpecPath]:
    """Extract repo-relative path references from validated SPEC sections.

    Args:
        spec_text: Full SPEC.md contents.

    Returns:
        Unique SPEC paths in first-seen order.

    Raises:
        TypeError: If ``spec_text`` is not a string.
        ValueError: If ``spec_text`` is empty.
    """
    _require_text(spec_text, "spec_text")

    paths: list[SpecPath] = []
    seen: set[str] = set()
    for heading in VALIDATED_SECTION_HEADINGS:
        for match in SPEC_PATH_PATTERN.finditer(_section_body(spec_text, heading)):
            value = match.group(1)
            if _is_repo_path(value) and value not in seen:
                paths.append(SpecPath(value))
                seen.add(value)
    return paths


def _path_violation(repo_root: Path, spec_path: SpecPath) -> SpecPathViolation | None:
    documented_path = spec_path.value
    actual_path = repo_root / documented_path.rstrip("/")
    if not actual_path.exists():
        return SpecPathViolation(documented_path, "documented path does not exist")
    if actual_path.is_dir() and not documented_path.endswith("/"):
        return SpecPathViolation(documented_path, "directory paths must end with /")
    if actual_path.is_file() and documented_path.endswith("/"):
        return SpecPathViolation(
            documented_path,
            "documented directory path resolves to a file",
        )
    return None


def validate_spec_paths(repo_root: Path, spec_path: Path) -> list[SpecPathViolation]:
    """Validate SPEC component paths against the repository filesystem.

    Args:
        repo_root: Repository root containing the documented paths.
        spec_path: SPEC.md file to inspect.

    Returns:
        Path violations in document order.

    Raises:
        TypeError: If arguments are not ``Path`` instances.
        FileNotFoundError: If ``repo_root`` or ``spec_path`` is missing.
    """
    _require_path(repo_root, "repo_root")
    _require_path(spec_path, "spec_path")
    if not repo_root.is_dir():
        raise FileNotFoundError(f"repo_root does not exist: {repo_root}")
    if not spec_path.is_file():
        raise FileNotFoundError(f"spec_path does not exist: {spec_path}")

    spec_text = spec_path.read_text(encoding="utf-8")
    violations: list[SpecPathViolation] = []
    for documented_path in extract_spec_paths(spec_text):
        violation = _path_violation(repo_root, documented_path)
        if violation is not None:
            violations.append(violation)
    return violations


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_default_repo_root(),
        help="Repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=None,
        help="SPEC.md path. Defaults to <repo-root>/SPEC.md.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the SPEC path validation command."""
    args = _parse_args(argv)
    repo_root = args.repo_root.resolve()
    spec_path = args.spec.resolve() if args.spec is not None else repo_root / "SPEC.md"
    violations = validate_spec_paths(repo_root, spec_path)
    if not violations:
        print("SPEC path validation passed.")
        return 0

    print("SPEC path validation failed:")
    for violation in violations:
        print(f"- {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
