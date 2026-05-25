import json
import pytest

from src.shared.python.sidekick.standalone.runner import run_calculator, EXIT_OK

@pytest.mark.integration
def test_wgs_reactor_end_to_end(tmp_path, capsys):
    inputs_path = tmp_path / "wgs_inputs.json"
    inputs_path.write_text(json.dumps({
        "temperature_c": 400.0,
        "co_fraction": 0.5,
        "h2o_fraction": 0.5,
        "co2_fraction": 0.0,
        "h2_fraction": 0.0,
        "pressure_bar": 20.0
    }))

    assert run_calculator("wgs_reactor", str(inputs_path)) == EXIT_OK
    out = capsys.readouterr().out
    result = json.loads(out)

    assert "extent_of_reaction" in result["values"]
    assert "co_conversion_fraction" in result["values"]
    assert "co_fraction" in result["values"]
    assert "co2_fraction" in result["values"]
    assert result["values"]["co_conversion_fraction"] > 0
