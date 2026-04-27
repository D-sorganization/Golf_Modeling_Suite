import glob


def clean_markers(content):
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if line.startswith("<<<<<<< HEAD"):
            continue
        if line.startswith("======="):
            # Only remove if it's exactly ======= or followed by whitespace
            if line.strip() == "=======":
                continue
        if line.startswith(">>>>>>>"):
            continue
        new_lines.append(line)
    return "\n".join(new_lines) + "\n"


for fpath in glob.glob(".github/workflows/*.yml"):
    # Skip ci-standard.yml and ci-optional-stack.yml as they have these in checks
    if "ci-standard.yml" in fpath or "ci-optional-stack.yml" in fpath:
        continue

    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    if any(m in content for m in ["<<<<<<<", "=======", ">>>>>>>"]):
        content = clean_markers(content)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
