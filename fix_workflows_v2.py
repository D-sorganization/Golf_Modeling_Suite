import glob
import re

fixed_pick_runner = """  pick-runner:
    runs-on: ubuntu-latest
    timeout-minutes: 2
    outputs:
      runner: ${{ steps.check.outputs.runner }}
    steps:
      - name: Check for self-hosted runner
        id: check
        env:
          GH_TOKEN: ${{ secrets.RUNNER_CHECK_TOKEN }}
        run: |
          ONLINE=$(gh api -H "Accept: application/vnd.github+json" /orgs/${{ github.repository_owner }}/actions/runners --paginate \\
            --jq 'if .runners then [.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length else 0 end' \\
            2>/dev/null || echo "0")
          if [[ "$ONLINE" =~ ^[0-9]+$ ]] && [[ "$ONLINE" -gt 0 ]]; then
            echo "runner=d-sorg-fleet" >> $GITHUB_OUTPUT
            echo "Self-hosted runner online - routing locally"
          else
            echo "runner=ubuntu-latest" >> $GITHUB_OUTPUT
            echo "No local self-hosted runner available; falling open to ubuntu-latest"
          fi
"""

pick_runner_regex = re.compile(
    r"  pick-runner:.*?(?=\n  [a-zA-Z0-9_-]+:|\Z)", re.DOTALL
)

for fpath in glob.glob(".github/workflows/*.yml"):
    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    # 1. Clean up conflict markers
    # This one matches even if it's at the end of the file
    content = re.sub(
        r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [^\n\s]*",
        r"\1",
        content,
        flags=re.DOTALL,
    )

    # 2. Replace pick-runner job
    if "  pick-runner:" in content:
        content = pick_runner_regex.sub(fixed_pick_runner.rstrip(), content)

    # 3. Ensure downstream jobs use the dynamic runner
    parts = re.split(r"^(  [a-zA-Z0-9_-]+:)", content, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        job_body = parts[i + 1]
        if "pick-runner" in job_body and "needs:" in job_body:
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

    content = "".join(parts)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
