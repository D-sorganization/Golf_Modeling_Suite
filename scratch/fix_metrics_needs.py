import os

metrics_path = '.github/workflows/Code-Metrics.yml'
if os.path.exists(metrics_path):
    with open(metrics_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if complexity-metrics job definition exists
    has_job_def = 'complexity-metrics:' in content and '    name: Complexity Analysis' in content
    
    if not has_job_def and 'complexity-metrics' in content:
        print('Fixing Code-Metrics.yml complexity-metrics references...')
        # Remove it from needs list
        content = content.replace('needs: [pick-runner, complexity-metrics, duplication-metrics]', 'needs: [pick-runner, duplication-metrics]')
        # Also fix summary if it needs it
        content = content.replace('needs: [pick-runner, complexity-metrics]', 'needs: pick-runner')
        
        with open(metrics_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Done.')
