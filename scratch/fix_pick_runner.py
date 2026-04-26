import os
import re

def fix_pick_runner(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Resolve any merge conflict markers first by picking the 'main' side
    # (usually the part after =======)
    # This is a bit risky but we know the 'main' side in this PR has the intended infra.
    # However, for pick-runner, they should be identical except for the fix.
    
    def resolve_conflicts(text):
        # Pattern for git conflict markers
        conflict_pattern = r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [^\n]+\n'
        # We'll pick the second part (main)
        return re.sub(conflict_pattern, r'\2\n', text, flags=re.DOTALL)

    new_content = resolve_conflicts(content)
    
    # 2. Fix the pick-runner job's gh api call
    # We'll look for the whole step or at least the ONLINE= part
    
    # This regex matches the online check with or without existing hardening or backslashes
    pattern = r'ONLINE=\$\(gh api.*?--jq\s+[\'\\]+.*?length.*?[\'\\]+\s+2>/dev/null \|\| echo "0"\)'
    
    replacement = r'ONLINE=$(gh api -H "Accept: application/vnd.github+json" /orgs/${{ github.repository_owner }}/actions/runners --paginate \\\n            --jq \'if .runners then [.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length else 0 end\' \\\n            2>/dev/null || echo "0")'
    
    new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)
    
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
            if fix_pick_runner(file_path):
                fixed_files.append(file_path)
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

print(f"Fixed {len(fixed_files)} files.")
