# engines.pendulum_models.tools.matlab_utilities.scripts.matlab_quality_check

MATLAB Quality Check Script

This script runs comprehensive quality checks on MATLAB code following the project's
.cursorrules.md requirements. It can be run from the command line and integrates
with the project's quality control system.

Usage:
    python scripts/matlab_quality_check.py [--strict] [--output-format json|text]

## Classes

### MATLABQualityChecker

Comprehensive MATLAB code quality checker.

#### Methods

##### check_matlab_files_exist
```python
def check_matlab_files_exist(self: Any) -> bool
```

Check if MATLAB files exist in the project.

Returns:
    True if MATLAB files are found, False otherwise

##### run_matlab_quality_checks
```python
def run_matlab_quality_checks(self: Any) -> dict[Any]
```

Run MATLAB quality checks using the MATLAB script.

Returns:
    Dictionary containing quality check results

##### run_all_checks
```python
def run_all_checks(self: Any) -> dict[Any]
```

Run all MATLAB quality checks.

Returns:
    Dictionary containing all quality check results
