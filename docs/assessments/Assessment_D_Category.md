# Assessment D Results

## Executive Summary
- Trademark risks in UI strings ("Kinematic Sequence").
- `opensim_gui.py` has no fallback.
- Extensive pass blocks in tests cause false sense of security.
## Findings
| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
|---|---|---|---|---|---|---|---|
| D-001 | Critical | UX | `opensim_gui.py` | Crash without OpenSim | No fallback | Add fallback | M |