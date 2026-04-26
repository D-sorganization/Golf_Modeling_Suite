import os
import re

PICK_RUNNER_JOB = """  pick-runner:
    runs-on: d-sorg-fleet
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
          if [[ "$ONLINE" -gt 0 ]]; then
            echo "runner=d-sorg-fleet" >> $GITHUB_OUTPUT
            echo "Self-hosted runner online — routing locally"
          else
            echo "::error::No local self-hosted runner available; failing closed"
            exit 1
          fi
"""

def fix_workflow(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the pick-runner job
    # We look for the pick-runner: key and replace until the next job or end of file
    # Job definition ends at the next line that starts with something other than spaces
    
    pattern = r'  pick-runner:.*?(\n\s*(\n|$)|(?=\n  [a-zA-Z]))'
    # That's tricky. Let's try to match from '  pick-runner:' to the start of the next job.
    
    new_content = re.sub(r'  pick-runner:.*?\n(?=  [a-zA-Z0-9_-]+:)', PICK_RUNNER_JOB, content, flags=re.DOTALL)
    
    # If no next job, it might be at the end
    if new_content == content:
        new_content = re.sub(r'  pick-runner:.*', PICK_RUNNER_JOB, content, flags=re.DOTALL)

    # Ensure runs-on: self-hosted is updated to use the runner output
    new_content = new_content.replace('runs-on: self-hosted', 'runs-on: ${{ needs.pick-runner.outputs.runner }}')

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

workflow_dir = '.github/workflows'
fixed_files = []
for filename in os.listdir(workflow_dir):
    if filename.endswith('.yml') or filename.endswith('.yaml'):
        file_path = os.path.join(workflow_dir, filename)
        try:
            if fix_workflow(file_path):
                fixed_files.append(file_path)
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

print(f"Fixed {len(fixed_files)} files.")
