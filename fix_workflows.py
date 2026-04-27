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

# Regex to find the whole pick-runner job
# It starts with '  pick-runner:' and ends before the next job (which starts at 2-space indentation)
# or end of string.
pick_runner_regex = re.compile(
    r"  pick-runner:.*?(?=\n  [a-zA-Z0-9_-]+:|\Z)", re.DOTALL
)

for fpath in glob.glob(".github/workflows/*.yml"):
    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    # 1. Clean up conflict markers first
    if "<<<<<<< HEAD" in content:
        # Simple heuristic: take the HEAD side
        # Conflict pattern: <<<<<<< HEAD\n(HEAD)\n=======\n(REMOTE)\n>>>>>>> (REVISION)
        content = re.sub(
            r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [^\n]+",
            r"\1",
            content,
            flags=re.DOTALL,
        )

    # 2. Replace pick-runner job
    if "  pick-runner:" in content:
        content = pick_runner_regex.sub(fixed_pick_runner.rstrip(), content)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
