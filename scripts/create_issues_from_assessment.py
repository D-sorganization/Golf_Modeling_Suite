#!/usr/bin/env python3

# ruff: noqa: E402

"""

Create GitHub issues from assessment findings using shared utilities.

"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.script_utils import run_main, setup_script_logging
from src.shared.python.assessment.analysis import classify_assessment_category

logger = setup_script_logging(__name__)


def _load_findings(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract assessment findings from the current or legacy summary schema."""
    findings = summary.get("issues")
    if findings is None:
        findings = summary.get("critical_issues", [])

    if not isinstance(findings, list):
        raise ValueError("Assessment summary issues must be a list")

    return [issue for issue in findings if isinstance(issue, dict)]


def _normalize_severity_filter(raw_severities: list[str]) -> set[str]:
    """Normalize severity filters while preserving an all-severities mode."""
    normalized = {severity.strip().upper() for severity in raw_severities if severity}
    if not normalized:
        return {"ALL"}
    return normalized


def _should_include_issue(issue: dict[str, Any], severities: set[str]) -> bool:
    """Check whether a finding should become an issue."""
    if "ALL" in severities:
        return True
    return issue.get("severity", "MAJOR").upper() in severities


def _build_issue_title(severity: str, category: str, description: str) -> str:
    """Create a stable issue title from the finding description."""
    clean_description = " ".join(description.split()) or "Assessment finding"
    snippet = clean_description[:90].rstrip()
    if len(clean_description) > 90:
        snippet = f"{snippet}..."
    return f"[GolfSuite] {severity} {category}: {snippet}"


def _write_output_file(
    output_file: Path,
    rows: list[dict[str, str]],
    source_file: Path,
) -> None:
    """Write a markdown staging report for generated issues."""
    lines = [
        "# Assessment Issue Staging Report",
        "",
        f"- Source summary: `{source_file}`",
        f"- Findings processed: {len(rows)}",
        "",
        "| Status | Severity | Category | Title | Source |",
        "|---|---|---|---|---|",
    ]

    for row in rows:
        lines.append(
            "| {status} | {severity} | {category} | {title} | {source} |".format(
                status=row["status"],
                severity=row["severity"],
                category=row["category"],
                title=row["title"].replace("|", "\\|"),
                source=row["source"].replace("|", "\\|"),
            )
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")


def get_existing_issues() -> list[dict[str, Any]]:
    """Fetch existing GitHub issues via 'gh' CLI."""

    try:
        res = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--limit",
                "200",
                "--json",
                "number,title,state,labels",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(res.stdout)

    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not fetch existing issues: {e}")

        return []


def create_issue(title: str, body: str, labels: list[str], dry_run: bool) -> bool:
    """Create a single GitHub issue."""

    if dry_run:
        logger.info(f"[DRY] Would create: {title}")

        return True

    try:
        cmd = ["gh", "issue", "create", "--title", title, "--body", body]

        if labels:
            cmd.extend(["--label", ",".join(labels)])

        subprocess.run(cmd, check=True, capture_output=True)

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create issue: {e.stderr}")

        return False


def process_findings(
    path: Path,
    sevs: list[str],
    check_exist: bool,
    dry_run: bool,
    output_file: Path | None = None,
) -> int:
    """Process findings from JSON and create corresponding issues."""

    if not path.exists():
        logger.error(f"Input file not found: {path}")

        return 1

    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error("Invalid assessment summary JSON: %s", e)
        return 1

    findings = _load_findings(summary)
    severity_filter = _normalize_severity_filter(sevs)
    selected = [
        issue for issue in findings if _should_include_issue(issue, severity_filter)
    ]

    existing = get_existing_issues() if check_exist else []
    existing_titles = {
        issue.get("title", "").strip().lower()
        for issue in existing
        if issue.get("state") == "OPEN" and issue.get("title")
    }

    staged_rows: list[dict[str, str]] = []
    had_failure = False

    for issue in selected:
        severity = issue.get("severity", "CRITICAL")

        desc = issue.get("description", "")

        source = issue.get("source", "Unknown")

        # Use shared classification logic
        cat = classify_assessment_category(source, desc)

        title = _build_issue_title(severity, cat, desc)

        if check_exist and title.lower() in existing_titles:
            logger.info(f"Skipping existing: {title}")
            status = "SKIPPED"
            staged_rows.append(
                {
                    "status": status,
                    "severity": severity,
                    "category": cat,
                    "title": title,
                    "source": source,
                }
            )
            continue

        body = f"## Issue Description\n\n**Severity**: {severity}\n**Category**: {cat}\n**Source**: {source}\n\n### Problem\n\n{desc}\n\n### Impact\n\nThis issue was identified during automated repository assessment.\n\n### Next Steps\n\n1. Investigate findings\n2. Determine root cause\n3. Implement fix\n\n---\n🤖 Auto-generated by Jules Assessment Tools"

        labels = [
            "auto-generated",
            "bug" if severity in ("BLOCKER", "CRITICAL") else "enhancement",
        ]

        if create_issue(title, body, labels, dry_run):
            status = "DRY-RUN" if dry_run else "CREATED"
        else:
            status = "FAILED"
            had_failure = True

        staged_rows.append(
            {
                "status": status,
                "severity": severity,
                "category": cat,
                "title": title,
                "source": source,
            }
        )

    if output_file is not None:
        _write_output_file(output_file, staged_rows, path)

    logger.info(
        "Processed %d findings (%d selected from %d total)",
        len(staged_rows),
        len(selected),
        len(findings),
    )

    if had_failure:
        return 1

    return 0


def main():
    """Parse arguments and create GitHub issues from assessment findings."""
    parser = argparse.ArgumentParser(description="Create GitHub issues from assessment")

    parser.add_argument("--input", required=True, type=Path)

    parser.add_argument(
        "--severity",
        default="ALL",
        help="Comma-separated severities to include, or ALL for every finding",
    )

    parser.add_argument("--check-existing", action="store_true")

    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument(
        "--output-file",
        type=Path,
        help="Optional markdown file to record the staged issue list",
    )

    args = parser.parse_args()

    sevs = [s.strip().upper() for s in args.severity.split(",")]

    return process_findings(
        args.input,
        sevs,
        args.check_existing,
        args.dry_run,
        args.output_file,
    )


if __name__ == "__main__":
    run_main(main, logger)
