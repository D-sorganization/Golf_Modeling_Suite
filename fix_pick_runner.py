import glob

for filepath in glob.glob(".github/workflows/*.yml"):
    with open(filepath, "r") as f:
        content = f.read()

    if 'GH_TOKEN: ${{ secrets.RUNNER_CHECK_TOKEN }}' in content:
        new_content = content.replace('GH_TOKEN: ${{ secrets.RUNNER_CHECK_TOKEN }}', 'GH_TOKEN: ${{ secrets.RUNNER_CHECK_TOKEN || github.token }}')

        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Updated {filepath}")
