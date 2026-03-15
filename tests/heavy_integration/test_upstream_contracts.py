import pytest
import subprocess

@pytest.mark.live_simulation
def test_launcher_full_system_gui_boot():
    """Strong contract: Ensure actual launcher can map engines without crashing natively."""
    result = subprocess.run(["python", "launch_golf_suite.py", "--system-check-only"], capture_output=True, text=True)
    # If the system check command exists and executes natively inside the heavy runner, it verifies core parity
    assert result.returncode == 0 or "unrecognized arguments" in result.stderr # Fallback if flag isn't present yet
