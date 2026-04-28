from pathlib import Path
import re
import datetime

spec_file = Path("SPEC.md")
content = spec_file.read_text()

version_match = re.search(r"\| (\d{4}-\d{2}-\d{2}) \| (\d+\.\d+\.\d+) \|", content)
if version_match:
    old_version = version_match.group(2)
    parts = old_version.split(".")
    new_version = f"{parts[0]}.{parts[1]}.{int(parts[2])+1}"
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # Replace Version in header (e.g. **Version:** 1.0.84)
    content = re.sub(r"\*\*Version:\*\* .*?\n", f"**Version:** {new_version}\n", content, count=1)

    # Add to change log
    log_entry = f"| {today} | {new_version}  | Bolt: Optimize ball simulator batched calculations using np.einsum |\n"
    content = content.replace("## 12. Change Log\n| Date       | Version | Changes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |\n| ---------- | ------- | ------------------------------------------------------------------------------------------------------------- |\n", f"## 12. Change Log\n| Date       | Version | Changes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |\n| ---------- | ------- | ------------------------------------------------------------------------------------------------------------- |\n{log_entry}")

    spec_file.write_text(content)
    print("SPEC.md updated")
else:
    print("Could not find version info")
