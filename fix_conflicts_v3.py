import glob
import re


def fix_conflicts(content):
    # Match conflict blocks and take the FIRST side (HEAD)
    # Pattern: <<<<<<< HEAD (anything) ======= (anything) >>>>>>> (anything)
    new_content = re.sub(
        r"<<<<<<< HEAD\s*(.*?)\s*=======\s*(.*?)\s*>>>>>>> [^\n\s]*",
        r"\1",
        content,
        flags=re.DOTALL,
    )
    return new_content


for fpath in glob.glob(".github/workflows/*.yml"):
    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    if "<<<<<<< HEAD" in content:
        content = fix_conflicts(content)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
