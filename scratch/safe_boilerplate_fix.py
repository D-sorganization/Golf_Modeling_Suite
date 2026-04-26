import os
import re

PICK_RUNNER_DEFINITION = """  pick-runner:
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
    
    # Replace the entire pick-runner job
    # We find '  pick-runner:' and replace until the next job or end of 'jobs:' section
    # Next job starts with '  ' and then non-space at the beginning of a line.
    
    # We look for the start of the job
    start_match = re.search(r'^  pick-runner:', content, re.MULTILINE)
    if not start_match:
        return False
        
    # We find the start of the NEXT job
    # A job starts with '  ' followed by alphanumeric and then ':'
    next_job_match = re.search(r'^  [a-zA-Z0-9_-]+:', content[start_match.end():], re.MULTILINE)
    
    if next_job_match:
        end_pos = start_match.end() + next_job_match.start()
        new_content = content[:start_match.start()] + PICK_RUNNER_DEFINITION + content[end_pos:]
    else:
        # It's the last job
        new_content = content[:start_match.start()] + PICK_RUNNER_DEFINITION
        # Wait, if it's the last job, we don't want to lose what's after it if it's not part of the job
        # But in GHA, jobs is the last section usually.
        # Let's be safer.
        # If there are no more jobs, there might still be something else (unlikely in GHA workflows)
        # We'll just assume it's the end of the file for now, or look for un-indented line.
        next_section_match = re.search(r'^[a-zA-Z]', content[start_match.end():], re.MULTILINE)
        if next_section_match:
             end_pos = start_match.end() + next_section_match.start()
             new_content = content[:start_match.start()] + PICK_RUNNER_DEFINITION + content[end_pos:]
        else:
             new_content = content[:start_match.start()] + PICK_RUNNER_DEFINITION

    # Also update runs-on: self-hosted if any exist
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
