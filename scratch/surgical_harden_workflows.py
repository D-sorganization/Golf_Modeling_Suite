import os

HARDENED_RUN_BLOCK = """        run: |
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
    
    new_lines = []
    in_pick_runner_run = False
    skip_lines = False
    
    for i, line in enumerate(lines):
        # Detect the start of the pick-runner run: block
        # We assume pick-runner job exists and has a run: block
        if 'pick-runner:' in line:
            new_lines.append(line)
            continue
            
        if 'run: |' in line and i > 0 and 'pick-runner' in "".join(lines[max(0, i-15):i]):
            new_lines.append(line)
            new_lines.append(HARDENED_RUN_BLOCK)
            in_pick_runner_run = True
            skip_lines = True
            continue
            
        if skip_lines:
            # Skip lines until we hit the next step or next job
            # Next step starts with - or next job starts with 2 spaces then a char
            if line.strip().startswith('-') or (line.startswith('  ') and not line.startswith('    ') and line.strip() and ':' in line):
                skip_lines = False
                in_pick_runner_run = False
            else:
                continue
        
        # Update runs-on: self-hosted
        if 'runs-on: self-hosted' in line:
            new_lines.append(line.replace('runs-on: self-hosted', 'runs-on: ${{ needs.pick-runner.outputs.runner }}'))
        else:
            new_lines.append(line)
            
    content = "".join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

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
