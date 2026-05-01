import os
import subprocess


def test_portfolio_demo_execution():
    """Verify the portfolio demo path runs without error and generates outputs."""
    script_path = os.path.join("scripts", "demo", "generate_portfolio_artifact.py")
    assert os.path.exists(script_path), f"Missing demo script at {script_path}"

    # Run the demo script with compiled Rust backend
    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True
    )

    # If the Rust backend isn't available, the script will fail.
    # We should skip the test if that's the case to avoid breaking standard CI.
    if result.returncode != 0 and "Rust kernel not found" in result.stderr:
        import pytest
        pytest.skip("Rust kernel not installed; skipping demo execution test.")

    # Otherwise, it should succeed
    assert result.returncode == 0, f"Demo script failed with error:\n{result.stderr}"

    # Check that the expected artifact was generated
    expected_output = os.path.join("output", "portfolio_demo", "kinematic_summary.json")
    assert os.path.exists(expected_output), f"Demo script did not generate expected artifact at {expected_output}"
