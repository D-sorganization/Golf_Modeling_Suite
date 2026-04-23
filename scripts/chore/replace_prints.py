"""Rewrite legacy print() calls in src/ to logger.info() during cleanup sweeps."""

from __future__ import annotations

import re
from pathlib import Path


def process_file(filepath: Path) -> bool:
    """Replace print() calls in a single file and inject logger scaffolding."""
    content = filepath.read_text(encoding="utf-8")

    if "opensim-models" in str(filepath):
        return False

    lines = content.split("\n")
    has_print = False
    new_lines: list[str] = []
    in_multiline_string = False

    for line in lines:
        stripped = line.strip()
        if stripped.count('"""') % 2 != 0 or stripped.count("'''") % 2 != 0:
            in_multiline_string = not in_multiline_string

        if (
            not in_multiline_string
            and not stripped.startswith("#")
            and re.search(r"(?<!\w)print\s*\(", line)
        ):
            line = re.sub(r"(?<!\w)print\s*\(", "logger.info(", line)
            has_print = True

        new_lines.append(line)

    if not has_print:
        return False

    result = "\n".join(new_lines)
    if "import logging" not in result:
        import_line = "import logging\nlogger = logging.getLogger(__name__)\n"
        if result.startswith('"""'):
            end_doc = result.find('"""', 3)
            if end_doc != -1:
                result = (
                    result[: end_doc + 3]
                    + "\n\n"
                    + import_line
                    + result[end_doc + 3 :]
                )
        else:
            result = import_line + "\n" + result
    elif "logger = logging.getLogger" not in result:
        result = result.replace(
            "import logging", "import logging\nlogger = logging.getLogger(__name__)"
        )

    filepath.write_text(result, encoding="utf-8")
    return True


def main() -> int:
    """Rewrite files under src/ and return the count of touched files."""
    repo_root = Path(__file__).resolve().parents[2]
    src_dir = repo_root / "src"
    count = 0
    for file_path in src_dir.rglob("*.py"):
        try:
            if process_file(file_path):
                count += 1
        except OSError:
            continue
    return count


if __name__ == "__main__":
    raise SystemExit(main())
