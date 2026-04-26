import os
import re

def fix_workflow(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Resolve conflict markers specifically for the pick-runner dispatcher pattern
    # Pattern: 
    # <<<<<<< HEAD
    # =======
    # ... content (main side) ...
    # >>>>>>> origin/main
    
    # This specifically looks for the conflict markers around steps:
    # and handles the case where the HEAD side is empty.
    
    conflict_pattern = r'<<<<<<< HEAD\s*=======\s*(.*?)\s*>>>>>>> origin/main'
    # Use re.DOTALL to match across lines
    new_content = re.sub(conflict_pattern, r'\1', content, flags=re.DOTALL)
    
    # 2. Fix pick-runner hardening (if not already fixed)
    # Handle the escaped backslashes \' if they exist
    pick_runner_pattern = r'ONLINE=\$\(gh api.*?--jq\s+[\'\\]+.*?length.*?[\'\\]+\s+2>/dev/null \|\| echo "0"\)'
    
    hardened_pick_runner = r'ONLINE=$(gh api -H "Accept: application/vnd.github+json" /orgs/${{ github.repository_owner }}/actions/runners --paginate \\\n            --jq \'if .runners then [.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length else 0 end\' \\\n            2>/dev/null || echo "0")'
    
    new_content = re.sub(pick_runner_pattern, hardened_pick_runner, new_content, flags=re.DOTALL)
    
    # 3. Fix runs-on: self-hosted to use the dispatcher output
    # But only for jobs that actually NEED the dispatcher (i.e. they are NOT pick-runner itself)
    # We'll look for runs-on: self-hosted
    
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
