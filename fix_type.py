with open('src/shared/python/humanoid_character_builder/mesh/_cg_primitive_fitting.py', 'r') as f:
    content = f.read()

import re
content = re.sub(
    r'quat = tuple\(rot\.as_quat\(\)\.tolist\(\)\)',
    r"q = rot.as_quat().tolist()\n        quat = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))",
    content
)

with open('src/shared/python/humanoid_character_builder/mesh/_cg_primitive_fitting.py', 'w') as f:
    f.write(content)
