"""Expose the tracked CI trigger token used during workflow debugging."""

from __future__ import annotations

CI_TRIGGER = "2026-04-20-upstreamdrift-required-checks-2"


def main() -> int:
    """Return success for manual inspection of the tracked trigger token."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
