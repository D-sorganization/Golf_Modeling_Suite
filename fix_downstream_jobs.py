import glob
import re

for fpath in glob.glob(".github/workflows/*.yml"):
    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    if "pick-runner" not in content:
        continue

    # Surgical fix for jobs that need pick-runner but have hardcoded runs-on
    # Matches:
    #   job-name:
    #     needs: [..., pick-runner, ...]
    #     runs-on: self-hosted (or others)

    # This regex is a bit complex to handle multi-line 'needs' and intermediate lines.
    # We'll split the content into jobs and process each.

    parts = re.split(r"^(  [a-zA-Z0-9_-]+:)", content, flags=re.MULTILINE)
    # parts[0] is everything before the first job
    # parts[1] is the first job name
    # parts[2] is the first job body

    changed = False
    for i in range(1, len(parts), 2):
        job_name = parts[i]
        job_body = parts[i + 1]

        if "pick-runner" in job_body and "needs:" in job_body:
            # Check if runs-on is hardcoded
            # We look for runs-on: (anything that isn't the dynamic variable)
            if (
                "runs-on:" in job_body
                and "${{ needs.pick-runner.outputs.runner }}" not in job_body
            ):
                job_body = re.sub(
                    r"(runs-on: ).*",
                    r"\1${{ needs.pick-runner.outputs.runner }}",
                    job_body,
                )
                parts[i + 1] = job_body
                changed = True

    if changed:
        new_content = "".join(parts)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
