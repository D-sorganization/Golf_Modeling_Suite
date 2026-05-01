import csv
from pathlib import Path

from scripts.generate_portfolio_demo_output import main


def test_generate_portfolio_demo_output(tmp_path: Path) -> None:
    output_csv = tmp_path / "test_output.csv"
    main(output_csv)
    assert output_csv.exists()
    with output_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) > 0
        quantities = {r["quantity"] for r in rows}
        assert "carry_distance" in quantities
