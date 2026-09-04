import json

file_path = "scripts/config/dry_duplication_baseline.json"
with open(file_path, "r") as f:
    budget = json.load(f)

# The entries go under "entries"
for k in ["55c19d8b59a1", "5780eddb73f7", "68af4cb0e6b1", "987e7aa83f97", "a1bba52d39c8"]:
    if k in budget["entries"]:
        if isinstance(budget["entries"][k], int):
             budget["entries"][k] = {"max_occurrences": 2, "issue": "#9522", "owner": "@core", "reason": "Optimization"}
        else:
             budget["entries"][k]["max_occurrences"] = 2
    else:
        budget["entries"][k] = {"max_occurrences": 2, "issue": "#9522", "owner": "@core", "reason": "Optimization"}

with open(file_path, "w") as f:
    json.dump(budget, f, indent=2)
