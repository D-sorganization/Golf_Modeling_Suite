import json

from src.shared.python.sidekick.standalone.runner import (
    EXIT_OK,
    EXIT_GENERIC,
    EXIT_VALIDATION,
    EXIT_UNKNOWN_CALCULATOR,
    run_calculator,
    register,
)
from src.shared.python.sidekick.protocols import CalculationResult, ValidationResult


# Setup fake calculators
def fake_validate(inputs):
    if inputs.get("invalid"):
        return ValidationResult(valid=False, errors=["fake validation error"])
    return ValidationResult(valid=True)


@register("fake_calc", validate=fake_validate)
def fake_calc(inputs):
    if inputs.get("crash"):
        raise ValueError("fake crash")
    return CalculationResult(
        values={"ans": inputs.get("val", 42)}, units={"ans": "fake_unit"}
    )


def test_run_calculator_ok(tmp_path, capsys):
    inputs_path = tmp_path / "inputs.json"
    inputs_path.write_text('{"val": 100}')

    assert run_calculator("fake_calc", str(inputs_path)) == EXIT_OK
    out = capsys.readouterr().out
    result = json.loads(out)
    assert result["values"]["ans"] == 100


def test_run_calculator_validation_failure(tmp_path, capsys):
    inputs_path = tmp_path / "inputs.json"
    inputs_path.write_text('{"invalid": true}')

    assert run_calculator("fake_calc", str(inputs_path)) == EXIT_VALIDATION
    err = capsys.readouterr().err
    result = json.loads(err)
    assert "fake validation error" in result["errors"]


def test_run_calculator_unknown_calc(tmp_path, capsys):
    inputs_path = tmp_path / "inputs.json"
    inputs_path.write_text("{}")

    assert run_calculator("fake_calx", str(inputs_path)) == EXIT_UNKNOWN_CALCULATOR
    err = capsys.readouterr().err
    result = json.loads(err)
    assert result["error"] == "Unknown calculator id"
    assert (
        "fake_calc" in result.get("suggestions", []) or result.get("suggestions") == []
    )


def test_run_calculator_crash(tmp_path):
    inputs_path = tmp_path / "inputs.json"
    inputs_path.write_text('{"crash": true}')

    assert run_calculator("fake_calc", str(inputs_path)) == EXIT_GENERIC


def test_run_calculator_csv(tmp_path, capsys):
    inputs_path = tmp_path / "inputs.json"
    inputs_path.write_text('{"val": 100}')

    assert run_calculator("fake_calc", str(inputs_path), fmt="csv") == EXIT_OK
    out = capsys.readouterr().out
    assert "key,value" in out
    assert "ans,100" in out
    assert "units,ans=fake_unit" in out


def test_no_pyqt_imports():
    import sys

    # test shouldn't load PyQt6 at all during the `test_run.py` run
    # but other conftest.py or test files might.
    # To truly test this, we should run a subprocess
    import subprocess

    cmd = [
        sys.executable,
        "-c",
        "import sys, os; sys.path.insert(0, os.path.abspath('src'));  from src.shared.python.sidekick.standalone.runner import run_calculator; "
        "assert not any('PyQt' in m for m in sys.modules), 'PyQt was imported'",
    ]
    subprocess.check_call(cmd)
