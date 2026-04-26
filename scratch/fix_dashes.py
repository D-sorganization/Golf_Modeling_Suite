import os
import re

workflow_dir = '.github/workflows'
for filename in os.listdir(workflow_dir):
    if filename.endswith('.yml') or filename.endswith('.yaml'):
        path = os.path.join(workflow_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Replace em-dash with regular dash (encoding safety)
        new_content = content.replace('—', ' - ')
        new_content = new_content.replace('–', ' - ')
        
        # 2. Fix pick-runner hardening (ensure no trailing spaces or weirdness)
        # Note: UpstreamDrift's ci-standard already has it, but others might not.
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Fixed encoding/dashes in {filename}')

# 3. Deep fix for Code-Metrics.yml
metrics_path = '.github/workflows/Code-Metrics.yml'
if os.path.exists(metrics_path):
    # I'll just write a known good version of Code-Metrics.yml
    pass # I'll do this in a separate tool call to be sure

# 4. Deep fix for release.yml
release_path = '.github/workflows/release.yml'
if os.path.exists(release_path):
    pass
