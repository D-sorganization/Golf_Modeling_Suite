import re

file_path = ".jules/bolt.md"
with open(file_path, "r") as f:
    content = f.read()

content = content.replace("## 2025-02-23 - Focus on Measurable Impact over Micro-Optimizations",
                          "## 2025-02-23 - Focus on Measurable Impact Over Micro-Optimizations")

with open(file_path, "w") as f:
    f.write(content)
