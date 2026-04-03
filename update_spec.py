import re

def update_spec():
    with open('SPEC.md', 'r') as f:
        content = f.read()

    # Find the Change Log section
    changelog_header = "## 12. Change Log"
    if changelog_header in content:
        # Revert the previous mess first
        content = re.sub(r'## 12\. Change Log\n\n\| Date \| Version \| Summary of Changes \|\n\|------\|---------\|--------------------\|\n\| 2026-04-03 \| 1\.0\.12 \|.*?\|\n', '## 12. Change Log\n', content)

        entry = "| 2026-04-03 | 1.0.12 | Performance optimization in `collision_generator.py`: optimized sphere radius calculation by replacing `np.linalg.norm(..., axis=1)` with delayed square root sum of squares. |\n"

        # Insert after the existing entries table
        # We need to find the correct table header
        table_header_regex = r'\| Date\s*\| Version\s*\| Summary of Changes\s*\|\n\|-*\|-*\|-*\|\n'
        match = re.search(table_header_regex, content)
        if match:
            table_header = match.group(0)
            content = content.replace(table_header, table_header + entry)
        else:
            print("Regex could not find table header in Change Log")
    else:
        print("Could not find Change Log section")

    with open('SPEC.md', 'w') as f:
        f.write(content)

    print("SPEC.md updated successfully.")

if __name__ == '__main__':
    update_spec()
