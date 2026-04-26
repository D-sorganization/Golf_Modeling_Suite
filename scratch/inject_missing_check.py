import os

CHECK_STEP = """      - name: Check for self-hosted runner
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
        lines = f.readlines()
    
    # Check if we need to fix it
    has_output = any('runner: ${{ steps.check.outputs.runner }}' in line for line in lines)
    has_check_id = any('id: check' in line for line in lines)
    
    if has_output and not has_check_id:
        new_lines = []
        in_steps = False
        for line in lines:
            new_lines.append(line)
            if 'steps:' in line and not in_steps:
                # We are assuming the first 'steps:' is for the pick-runner job
                # This is safe because pick-runner is always first.
                new_lines.append(CHECK_STEP)
                in_steps = True
        
        content = "".join(new_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
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
