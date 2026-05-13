import pytest

with open("tests/integration/test_urdf_cross_engine_fk.py", "r") as f:
    content = f.read()

content = content.replace("            results[i, b] = data.xpos[bid]", "            results[i, b] = data.xpos[bid]\n            if bid == -1:\n                print(f'Body {body_names[b]} not found in mj')")

with open("tests/integration/test_urdf_cross_engine_fk.py", "w") as f:
    f.write(content)
