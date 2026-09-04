import re

with open("SPEC.md", "r") as f:
    content = f.read()

# Replace double entry with single entry
new_content = content.replace(
    "| 2026-09-04 | #9522      | (spec-exempt: micro-optimization) Optimize bounding sphere magnitude calculation with np.einsum |\n| 2026-09-04 | #9522      | (spec-exempt: micro-optimization) Optimize bounding sphere magnitude calculation with np.einsum |",
    "| 2026-09-04 | #9522      | (spec-exempt: micro-optimization) Optimize bounding sphere magnitude calculation with np.einsum |",
    1
)


with open("SPEC.md", "w") as f:
    f.write(new_content)
