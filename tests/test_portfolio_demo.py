import os
import subprocess


def test_portfolio_demo_execution():
    """Verify the portfolio demo path runs without error and generates outputs."""
    script_path = os.path.join("scripts", "demo", "generate_portfolio_artifact.py")
    assert os.path.exists(script_path), f"Missing demo script at {script_path}"

    # Run the demo script
    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True
    )

    # Check that it executed successfully
    assert result.returncode == 0, f"Demo script failed with error:\n{result.stderr}"

    # Check that the expected artifact was generated
    expected_output = os.path.join("output", "portfolio_demo", "kinematic_summary.json")
    assert os.path.exists(expected_output), f"Demo script did not generate expected artifact at {expected_output}"
