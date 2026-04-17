import re

with open("SPEC.md", "r") as f:
    content = f.read()

# Update Spec Version
match = re.search(r"\|\s*\*\*Spec Version\*\*\s*\|\s*([\d\.]+)\s*\|", content)
if match:
    old_version = match.group(1)
    parts = old_version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    new_version = '.'.join(parts)
    content = content.replace(f"| **Spec Version**        | {old_version} ", f"| **Spec Version**        | {new_version} ")

# Add to Changelog / Change Log (append to end of file)
content += f"\n- $(date +%Y-%m-%d): Bolt: Replaced np.linalg.norm with math.sqrt(np.dot) in collision_checker.py for performance optimization\n"

with open("SPEC.md", "w") as f:
    f.write(content)
