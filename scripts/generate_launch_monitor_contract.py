"""Generate the published launch-monitor analysis contract v2 JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path

from src.shared.python.launch_monitor import contract_v2_json_schema


def main() -> None:
    """Write the deterministic schema artifact from the Python authority."""

    root = Path(__file__).resolve().parents[1]
    destination = (
        root / "docs" / "api" / "contracts" / "launch-monitor-analysis-v2.schema.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(contract_v2_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
