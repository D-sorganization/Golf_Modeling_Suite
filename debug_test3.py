import pytest

with open("tests/integration/test_urdf_cross_engine_fk.py", "r") as f:
    content = f.read()

content = content.replace("assert max_rmse <= 0.005", "print(f'\\nbody_names={body_names}'); assert max_rmse <= 0.005")

with open("tests/integration/test_urdf_cross_engine_fk.py", "w") as f:
    f.write(content)
