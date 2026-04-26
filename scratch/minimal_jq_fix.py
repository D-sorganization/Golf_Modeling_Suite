import os

TARGET_JQ = '[.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length'
HARDENED_JQ = 'if .runners then [.runners[] | select(.status == "online") | select(.labels[].name == "d-sorg-fleet")] | length else 0 end'

def fix_workflow(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We replace the JQ pattern. We need to handle both escaped and unescaped versions.
    new_content = content.replace(f"--jq '{TARGET_JQ}'", f"--jq '{HARDENED_JQ}'")
    new_content = new_content.replace(f"--jq \\'{TARGET_JQ}\\'", f"--jq '{HARDENED_JQ}'")
    
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
