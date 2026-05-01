import csv
from pathlib import Path

from scripts.generate_golf_modeling_demo_output import generate_output


def test_generate_golf_modeling_demo_output(tmp_path: Path) -> None:
    output_path = tmp_path / "test_output.csv"
    generate_output(output_path)

    assert output_path.exists()

    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 9

    carry_m_rows = [
        row
        for row in rows
        if row["quantity"] == "carry_distance" and row["unit"] == "m"
    ]
    assert len(carry_m_rows) == 1
    assert float(carry_m_rows[0]["value"]) > 100.0
