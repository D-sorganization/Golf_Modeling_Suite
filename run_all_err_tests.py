import pytest
tests = [
    "tests/unit/engines/pinocchio/test_screw_kinematics.py",
    "tests/unit/engines/opensim/test_screw_kinematics.py",
    "tests/unit/test_pinocchio_gui.py",
    "tests/launchers/test_golf_suite_launcher.py",
    "tests/unit/shared_python/test_engine_loaders_coverage.py",
    "tests/unit/engines/mujoco/test_urdf_io.py",
    "tests/unit/engines/mujoco/test_video_export.py",
    "tests/unit/engines/opensim/test_muscle_conditioning.py",
    "tests/unit/test_launch_golf_suite.py"
]
pytest.main(tests + ["-v"])
