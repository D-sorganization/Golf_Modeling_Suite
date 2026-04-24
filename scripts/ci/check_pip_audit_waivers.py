#!/usr/bin/env python3
"""Validate and load pip-audit waivers from .github/security/pip-audit-ignore.yml.

This script enforces expiry-based waiver management:
- Loads waivers from the structured YAML file
- Checks that no waivers have expired
- Generates pip-audit --ignore-vuln flags for active waivers
- Fails CI if any waiver has passed its expiry date (stale waiver guard)

Usage:
    python scripts/ci/check_pip_audit_waivers.py [--json]

Output:
    Prints space-separated --ignore-vuln flags for use in pip-audit command
    With --json, prints JSON with status and waivers

Exit codes:
    0: All waivers valid and within expiry
    1: Waiver validation failed or waiver has expired
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "ERROR: pyyaml not installed. Install with: pip install pyyaml", file=sys.stderr
    )
    sys.exit(1)


def load_waivers(waiver_file: Path) -> dict:
    """Load waivers from YAML file.

    Args:
        waiver_file: Path to .github/security/pip-audit-ignore.yml

    Returns:
        Dictionary with 'waivers' key containing list of waiver dicts
    """
    if not waiver_file.exists():
        print(f"ERROR: Waiver file not found: {waiver_file}", file=sys.stderr)
        sys.exit(1)

    with open(waiver_file, encoding="utf-8") as f:
        content = yaml.safe_load(f)

    if not content or not isinstance(content, dict):
        print("ERROR: Invalid YAML structure", file=sys.stderr)
        sys.exit(1)

    return content


def check_expiry(waivers: list) -> tuple[list, list]:
    """Check waiver expiry dates and separate active from expired.

    Args:
        waivers: List of waiver dictionaries

    Returns:
        Tuple of (active_waivers, expired_waivers)
    """
    now = datetime.now(timezone.utc)
    active = []
    expired = []

    for waiver in waivers:
        if "expires_at" not in waiver:
            print(
                f"WARNING: Waiver {waiver.get('id', 'UNKNOWN')} missing expires_at",
                file=sys.stderr,
            )
            active.append(waiver)
            continue

        try:
            # Try parsing ISO format (YYYY-MM-DD)
            expiry_str = waiver["expires_at"]
            if isinstance(expiry_str, str):
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            else:
                # Try treating as date object from YAML parsing
                expiry_date = datetime.combine(expiry_str, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                )

            if now >= expiry_date:
                expired.append(waiver)
            else:
                active.append(waiver)
        except (ValueError, AttributeError) as e:
            print(
                f"ERROR: Invalid expiry date for {waiver.get('id', 'UNKNOWN')}: "
                f"{waiver.get('expires_at')} — {e}",
                file=sys.stderr,
            )
            sys.exit(1)

    return active, expired


def main():
    """Main entry point."""
    # Determine waiver file path
    root = Path(__file__).parent.parent.parent  # Scripts -> UpstreamDrift root
    waiver_file = root / ".github" / "security" / "pip-audit-ignore.yml"

    # Load waivers
    content = load_waivers(waiver_file)
    waivers = content.get("waivers", [])

    if not waivers:
        print("No waivers defined.", file=sys.stderr)
        sys.exit(0)

    # Check expiry
    active, expired = check_expiry(waivers)

    # Report expired waivers
    if expired:
        print("ERROR: The following waivers have expired:", file=sys.stderr)
        for waiver in expired:
            print(
                f"  {waiver['id']}: expires_at {waiver.get('expires_at', 'UNKNOWN')}",
                file=sys.stderr,
            )
        sys.exit(1)

    # Generate pip-audit flags for active waivers
    ignore_flags = " ".join(f"--ignore-vuln {w['id']}" for w in active)

    # Handle JSON output
    if "--json" in sys.argv:
        output = {
            "status": "ok",
            "active_waivers": len(active),
            "waivers": active,
            "ignore_flags": ignore_flags,
        }
        print(json.dumps(output, indent=2))
    else:
        print(ignore_flags)

    sys.exit(0)


if __name__ == "__main__":
    main()
