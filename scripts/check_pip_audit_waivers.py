"""Check that all pip-audit waivers in pip_audit_waivers.json are still current.

Exits 1 with an error message if any waiver has an expiry date in the past.
Exits 0 if all waivers are current or the file contains no waivers.
"""

import json
import sys
from datetime import date
from pathlib import Path

WAIVERS_FILE = Path(__file__).parent / "config" / "pip_audit_waivers.json"


def main() -> int:
    if not WAIVERS_FILE.exists():
        print(f"Waiver file not found: {WAIVERS_FILE}", file=sys.stderr)
        return 1

    with WAIVERS_FILE.open() as fh:
        data = json.load(fh)

    waivers = data.get("waivers", [])
    if not waivers:
        print("No pip-audit waivers defined; nothing to check.")
        return 0

    today = date.today()
    expired = []
    for waiver in waivers:
        vuln_id = waiver.get("vuln_id", "<unknown>")
        expires_str = waiver.get("expires", "")
        if not expires_str:
            expired.append(f"  {vuln_id}: missing 'expires' field")
            continue
        try:
            expires = date.fromisoformat(expires_str)
        except ValueError:
            expired.append(f"  {vuln_id}: invalid 'expires' value '{expires_str}'")
            continue
        if expires < today:
            ticket = waiver.get("ticket", "no ticket")
            expired.append(
                f"  {vuln_id}: expired {expires_str}"
                f" — reason: {waiver.get('reason', '')}"
                f" — ticket: {ticket}"
            )

    if expired:
        print(
            "ERROR: The following pip-audit waivers have expired."
            " Renew, fix, or remove them:\n",
            file=sys.stderr,
        )
        for line in expired:
            print(line, file=sys.stderr)
        return 1

    print(f"All {len(waivers)} pip-audit waiver(s) are current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
