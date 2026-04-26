import os
import re

workflow_dir = '.github/workflows'
for filename in os.listdir(workflow_dir):
    if filename.endswith('.yml') or filename.endswith('.yaml'):
        path = os.path.join(workflow_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace banned tokens
        new_content = content.replace('runs-on: self-hosted', 'runs-on: d-sorg-fleet')
        
        # Hardened pick-runner pattern
        # This matches the existing pattern and ensures it's hardened.
        generic_pick_pattern = r'ONLINE=\$\(gh api.*?/orgs/\$\{\{ github\.repository_owner \}\}/actions/runners.*?2>/dev/null \|\| echo \"0\"\)'
        
        hardened_replacement = 'ONLINE=$(gh api -H "Accept: application/vnd.github+json" /orgs/${{ github.repository_owner }}/actions/runners --paginate \\\n            --jq \'if .runners then [.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length else 0 end\' \\\n            2>/dev/null || echo "0")'
        
        new_content = re.sub(generic_pick_pattern, hardened_replacement, new_content, flags=re.DOTALL)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Fixed {filename}')

# Specifically fix Code-Metrics.yml complexity-metrics issue
metrics_path = '.github/workflows/Code-Metrics.yml'
if os.path.exists(metrics_path):
    with open(metrics_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'complexity-metrics' not in content and 'needs: [pick-runner, complexity-metrics, duplication-metrics]' in content:
        print('Fixing Code-Metrics.yml complexity-metrics reference...')
        new_content = content.replace('needs: [pick-runner, complexity-metrics, duplication-metrics]', 'needs: [pick-runner, duplication-metrics]')
        with open(metrics_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
