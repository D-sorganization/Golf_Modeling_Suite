import subprocess

p = subprocess.run(["python", "launch_golf_suite.py", "--classic"], capture_output=True)
print("STDOUT:")
print(p.stdout.decode("utf-8", errors="ignore"))
print("STDERR:")
print(p.stderr.decode("utf-8", errors="ignore"))
print(f"EXIT CODE: {p.returncode}")
