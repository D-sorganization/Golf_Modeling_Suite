import os
import re

files_to_patch = [
    "src/shared/python/physics/impact_model/models.py",
    "src/shared/python/physics/ground_reaction_forces.py",
    "src/shared/python/physics/_impact_physics.py"
]

def format_replacement(var_name):
    var_name = var_name.strip()
    return f"(0.0 if np.asarray({var_name}, dtype=float).reshape(-1).size == 0 else math.hypot(*np.asarray({var_name}, dtype=float).reshape(-1)))"

for filepath in files_to_patch:
    with open(filepath, 'r') as f:
        content = f.read()

    new_content = re.sub(r'np\.linalg\.norm\(([^)]+)\)', lambda m: m.group(0) if '...' in m.group(1) else format_replacement(m.group(1)), content)

    # Note: we need to ensure math is imported
    if "import math" not in new_content:
        # Find where to put it. Best to put it after import numpy as np
        new_content = re.sub(r'(import numpy as np)', r'\1\nimport math', new_content, count=1)

    with open(filepath, 'w') as f:
        f.write(new_content)

print("Done")
