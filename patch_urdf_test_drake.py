import pytest

with open("tests/integration/test_urdf_cross_engine_fk.py", "r") as f:
    content = f.read()

content = content.replace("                results[i, b] = pose.translation()", "                results[i, b] = pose.translation()\n            else:\n                print(f'Body {bname} not found in drake')")

with open("tests/integration/test_urdf_cross_engine_fk.py", "w") as f:
    f.write(content)
