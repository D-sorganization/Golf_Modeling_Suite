"""Verify that all file/directory paths referenced in SPEC.md exist on disk.

Exits 0 if all referenced paths exist; exits 1 and prints the broken paths
otherwise.

Usage:
    python3 scripts/check_spec_paths.py
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = REPO_ROOT / "SPEC.md"

# Match backtick-quoted tokens on a single line that look like repo-relative
# paths. We require the path to start with a recognised top-level directory
# so that inline code snippets (e.g. ``GET /health``) are not mistaken for
# paths. We intentionally match only within a single line to avoid spanning
# across table cells or fenced code blocks.
_TOP_LEVEL_DIRS = (
    "src/",
    "scripts/",
    "tests/",
    "rust_core/",
    "shared/",
    "ui/",
    "docs/",
    "config/",
    "apps/",
    "assets/",
    "data/",
)

# Matches a single backtick-delimited token that does NOT contain a newline.
_INLINE_BACKTICK_RE = re.compile(r"`([^`\n]+)`")


def _looks_like_path(token: str) -> bool:
    """Return True when *token* looks like a repo-relative file/directory path."""
    return any(token.startswith(prefix) for prefix in _TOP_LEVEL_DIRS)


def _in_fenced_block(line: str, inside_fence: bool) -> bool:
    """Return True when the line is a fence delimiter (``` or ~~~)."""
    stripped = line.strip()
    return stripped.startswith(("```", "~~~"))


def collect_paths(spec_text: str) -> list[str]:
    """Return every repo-relative path found in backticks inside *spec_text*.

    Lines inside fenced code blocks are skipped because those blocks describe
    illustrative directory trees rather than authoritative path references.
    """
    found: list[str] = []
    inside_fence = False

    for line in spec_text.splitlines():
        if _in_fenced_block(line, inside_fence):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        for match in _INLINE_BACKTICK_RE.finditer(line):
            token = match.group(1).strip()
            if _looks_like_path(token) and token not in found:
                found.append(token)

    return found


def main() -> int:
    if not SPEC_FILE.exists():
        print(f"ERROR: SPEC.md not found at {SPEC_FILE}", file=sys.stderr)
        return 1

    spec_text = SPEC_FILE.read_text(encoding="utf-8")
    paths = collect_paths(spec_text)

    if not paths:
        print("No repo-relative paths found in SPEC.md.")
        return 0

    broken: list[str] = []
    for rel_path in paths:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            broken.append(rel_path)

    if broken:
        print("SPEC.md references paths that do not exist on disk:")
        for p in broken:
            print(f"  MISSING: {p}")
        return 1

    print(f"All {len(paths)} path(s) referenced in SPEC.md exist on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
