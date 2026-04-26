import os
import re

def fix_workflow(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_conflict = False
    head_side = True
    
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_conflict = True
            head_side = True
            continue
        elif line.startswith('======='):
            head_side = False
            continue
        elif line.startswith('>>>>>>> origin/main'):
            in_conflict = False
            continue
        
        if in_conflict:
            if not head_side:
                new_lines.append(line)
            # if head_side, we skip it
        else:
            new_lines.append(line)
    
    content = "".join(new_lines)
    
    # Fix pick-runner hardening
    # This time without escaping unless needed
    pick_runner_pattern = r'ONLINE=\$\(gh api.*?--jq\s+[\'\\]+.*?length.*?[\'\\]+\s+2>/dev/null \|\| echo "0"\)'
    
    hardened_pick_runner = r'ONLINE=$(gh api -H "Accept: application/vnd.github+json" /orgs/${{ github.repository_owner }}/actions/runners --paginate \\\n            --jq \'if .runners then [.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length else 0 end\' \\\n            2>/dev/null || echo "0")'
    
    content = re.sub(pick_runner_pattern, hardened_pick_runner, content, flags=re.DOTALL)
    
    # Fix runs-on: self-hosted
    content = content.replace('runs-on: self-hosted', 'runs-on: ${{ needs.pick-runner.outputs.runner }}')
    
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
