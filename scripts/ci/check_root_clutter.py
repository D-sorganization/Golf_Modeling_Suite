"""CI guard: fail if debris files exist at the repo root.

Blocked patterns (repo root only):
  - *.bak
  - pr_body_*.md
  - .ci_trigger*.py
  - fix_*.py
  - package.json that contains "react-scripts" (Create React App artifact)

Exit 0 if clean, exit 1 with a descriptive message if clutter is found.
"""

import fnmatch
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Simple glob patterns matched against filenames at repo root
BLOCKED_GLOB_PATTERNS = [
    "*.bak",
    "pr_body_*.md",
    ".ci_trigger*.py",
    "fix_*.py",
]


def _matches_any_glob(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in BLOCKED_GLOB_PATTERNS)


def _is_cra_package_json(path: Path) -> bool:
    """Return True if path is a package.json that contains 'react-scripts'."""
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    deps: dict = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("devDependencies", {}))
    return "react-scripts" in deps


def main() -> int:
    violations: list[str] = []

    for entry in REPO_ROOT.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        if _matches_any_glob(name):
            violations.append(
                f"  {name}  — matches blocked pattern (debris file at repo root)"
            )
        elif name == "package.json" and _is_cra_package_json(entry):
            violations.append(
                f"  {name}  — contains 'react-scripts'; "
                "this is a deprecated CRA artifact and must be removed"
            )

    if violations:
        print("ERROR: Repo-root clutter detected (issues #3836, #3846):")
        for msg in violations:
            print(msg)
        print(
            "\nRemove these files and do not commit them to the repository.\n"
            "Legitimate package.json files belong under ui/ (Vite/Tauri build)."
        )
        return 1

    print("check_root_clutter: OK — no debris files found at repo root.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
