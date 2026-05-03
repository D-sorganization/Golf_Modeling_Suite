#!/usr/bin/env python3
"""Enforce line-count budgets for changed Python files with owned exceptions."""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("scripts/config/file_size_budget.json")
MAX_EXCEPTIONS = 5
MAX_EXCEPTION_DAYS = 90
WATCHLIST_RATIO = 0.9


class CodeownersRule(NamedTuple):
    """Parsed CODEOWNERS rule with the owner group used for budget routing."""

    pattern: str
    owner: str


class WatchlistEntry(NamedTuple):
    """Tracked Python file nearing the line-count cap."""

    path: str
    line_count: int
    owner: str


def _repo_root() -> Path:
    """Return the repository root for this script."""
    return Path(__file__).resolve().parents[2]


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


def _load_config(repo_root: Path, config_path: Path) -> dict:
    with (repo_root / config_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _changed_python_files(repo_root: Path, base_ref: str) -> list[Path]:
    output = _run_git(["diff", "--name-only", f"{base_ref}...HEAD", "--"], repo_root)
    return [
        repo_root / path
        for path in output.splitlines()
        if path.endswith(".py") and (repo_root / path).exists()
    ]


def _tracked_python_files(repo_root: Path) -> list[Path]:
    output = _run_git(["ls-files", "*.py"], repo_root)
    return [
        repo_root / path
        for path in output.splitlines()
        if path.endswith(".py") and (repo_root / path).exists()
    ]


def _exception_is_active(exc: dict, today: date | None = None) -> bool:
    expires_on = exc.get("expires_on")
    if not expires_on:
        return True
    effective_today = today or date.today()
    return effective_today <= date.fromisoformat(expires_on)


def _exception_expires_within_limit(exc: dict, today: date) -> bool:
    expires_on = exc.get("expires_on")
    if not expires_on:
        return False
    return (date.fromisoformat(expires_on) - today).days <= MAX_EXCEPTION_DAYS


def _line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _collect_active_exceptions(
    config: dict, today: date | None = None
) -> tuple[dict[str, dict], list[str]]:
    active_exceptions: dict[str, dict] = {}
    invalid_exceptions: list[str] = []
    effective_today = today or date.today()

    exceptions = config.get("exceptions", [])
    if len(exceptions) > MAX_EXCEPTIONS:
        invalid_exceptions.append(
            f"Too many file-size exceptions: {len(exceptions)} entries "
            f"(maximum={MAX_EXCEPTIONS})"
        )
        return active_exceptions, invalid_exceptions

    for exc in exceptions:
        path = str(exc.get("path", "")).strip()
        owner = str(exc.get("owner", "")).strip()
        reason = str(exc.get("reason", "")).strip()
        if not path or not owner or not reason:
            invalid_exceptions.append(f"Invalid exception entry: {exc}")
            continue
        try:
            if _exception_is_active(
                exc, effective_today
            ) and _exception_expires_within_limit(exc, effective_today):
                active_exceptions[path] = exc
            elif _exception_is_active(exc, effective_today):
                invalid_exceptions.append(
                    f"Exception window too long: {path} "
                    f"(owner={owner}, expires_on={exc.get('expires_on')}, "
                    f"maximum_days={MAX_EXCEPTION_DAYS})"
                )
            else:
                invalid_exceptions.append(
                    f"Expired exception: {path} (owner={owner}, expires_on={exc.get('expires_on')})"
                )
        except ValueError:
            invalid_exceptions.append(
                f"Invalid expires_on date in exception: {path} ({exc.get('expires_on')})"
            )

    return active_exceptions, invalid_exceptions


def _load_codeowners(repo_root: Path) -> list[CodeownersRule]:
    codeowners_path = repo_root / ".github" / "CODEOWNERS"
    if not codeowners_path.exists():
        return []

    rules: list[CodeownersRule] = []
    for raw_line in codeowners_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        rules.append(CodeownersRule(pattern=parts[0], owner=parts[1]))
    return rules


def _codeowners_pattern_matches(pattern: str, rel_path: str) -> bool:
    normalized = pattern.strip()
    if not normalized:
        return False
    anchored = normalized.startswith("/")
    normalized = normalized.lstrip("/")
    if normalized.endswith("/"):
        return rel_path.startswith(normalized)
    if any(token in normalized for token in "*?[]"):
        return fnmatch.fnmatch(rel_path, normalized)
    if anchored:
        return rel_path == normalized
    return rel_path == normalized or rel_path.endswith(f"/{normalized}")


def _owner_for_path(rel_path: str, codeowners: list[CodeownersRule]) -> str:
    owner = "@unowned"
    for rule in codeowners:
        if _codeowners_pattern_matches(rule.pattern, rel_path):
            owner = rule.owner
    return owner


def _collect_watchlist(
    repo_root: Path,
    files: list[Path],
    budget: int,
    codeowners: list[CodeownersRule],
) -> list[WatchlistEntry]:
    threshold = int(budget * WATCHLIST_RATIO)
    entries: list[WatchlistEntry] = []
    for file_path in files:
        rel = str(file_path.relative_to(repo_root)).replace("\\", "/")
        if rel.startswith("tests/"):
            continue
        count = _line_count(file_path)
        if threshold <= count <= budget:
            entries.append(
                WatchlistEntry(
                    path=rel,
                    line_count=count,
                    owner=_owner_for_path(rel, codeowners),
                )
            )
    return sorted(entries, key=lambda entry: (-entry.line_count, entry.path))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enforce changed-file line-count budget."
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to JSON config relative to repository root.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref used for changed-file detection.",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    config = _load_config(repo_root, args.config_path)
    budget = int(config.get("max_lines", 1200))

    active_exceptions, invalid_exceptions = _collect_active_exceptions(config)
    codeowners = _load_codeowners(repo_root)

    try:
        changed_files = _changed_python_files(repo_root, args.base_ref)
    except RuntimeError:
        changed_files = _changed_python_files(repo_root, "HEAD~1")

    violations = list(invalid_exceptions)
    for file_path in changed_files:
        rel = str(file_path.relative_to(repo_root)).replace("\\", "/")
        if rel.startswith("tests/"):
            continue
        if rel in active_exceptions:
            continue
        count = _line_count(file_path)
        if count > budget:
            violations.append(f"{rel}: {count} lines (budget={budget})")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    watchlist = _collect_watchlist(
        repo_root=repo_root,
        files=_tracked_python_files(repo_root),
        budget=budget,
        codeowners=codeowners,
    )
    if watchlist:
        logger.info("WATCHLIST: files within 90%% of file-size budget:")
        for entry in watchlist:
            logger.info(
                "  %s: %s lines (owner=%s)", entry.path, entry.line_count, entry.owner
            )

    if violations:
        logger.error("FAIL: file size budget violations detected:\n")
        for violation in violations:
            logger.error("  %s", violation)
        logger.error(
            "\nSplit orchestration/domain/IO concerns or add owned, expiring exception."
        )
        return 1

    logger.info("OK: Changed files are within line-count budget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
