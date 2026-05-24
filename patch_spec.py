with open("SPEC.md", "r") as f:
    content = f.read()

# I will append the headless runner note to the sidekick section
if "sidekick run --calculator" not in content:
    content = content.replace("## 7. Feature Status", "## 7. Feature Status\n- **Sidekick Headless Runner**: Added `sidekick run --calculator` shell scriptability to execute calculations headlessly.")
    with open("SPEC.md", "w") as f:
        f.write(content)
