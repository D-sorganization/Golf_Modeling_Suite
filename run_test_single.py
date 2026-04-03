import pytest
import sys
tests = [
    "tests/launchers/test_golf_suite_launcher.py"
]
sys.exit(pytest.main(tests + ["-v"]))
