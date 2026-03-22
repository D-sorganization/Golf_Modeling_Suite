# Assessment K Results: Reproducibility & Provenance

## Executive Summary

- Reproducibility and determinism are formally centralized through `src/shared/python/data_io/reproducibility.py` and `logger_utils.py`, showcasing a mature approach to random seed management across Python, NumPy, PyTorch, and environment hashes.
- Despite strong environmental hashing, reproducibility fails severely in practice due to the lack of dependency pinning in the `requirements.txt` / `pyproject.toml` files, alongside conditional imports (`try...except ImportError`) related to `opensim` and `sklearn`.
- The `pytest` test suite leverages random seeds successfully to assert numeric equality, but fails to account for floating-point non-determinism inside `src/shared/python/physics/flexible_shaft.py` and `src/engines/physics_engines/mujoco/`.
- Experiment tracking lacks automated metadata integration (such as MLflow or WandB) for the extensive parameter sweeps found in `multi_param_analysis/` and `optimizer_gui/`.

## Top 10 Data Handling & Provenance Risks

1. **Critical:** Loose versioning of critical analytical dependencies (`scipy`, `fastapi`, `numpy`) causing cross-environment irreproducibility.
2. **Critical:** Missing `opensim` installation pathways leading to deterministic test breaks depending entirely on local developer OS and conda environments.
3. **Major:** Parameter sweeps lack automated experiment metadata provenance (e.g., git hash, parameters used, hardware specs). Outputs rely solely on localized `.csv` or `.mat` artifact drops.
4. **Major:** Floating-point determinism is lost within complex MuJoCo simulations, causing slightly drifting `.xml` template generations over long time steps.
5. **Minor:** The `# type: ignore` suppressions around `np.random` and `torch.manual_seed` hide deterministic propagation errors from `mypy`.
6. **Minor:** Data processing logic does not log file checksums prior to loading datasets, leaving the door open for untracked silent data corruption.
7. **Minor:** Lack of explicit encoding declarations (e.g. `UP015` violations) causes divergent string reading on Windows vs. Linux.
8. **Minor:** Hardcoded "latest" tags on Docker images pulling from untracked caches, causing execution drift.
9. **Minor:** `src/api/auth/security.py`'s stub implementation bypasses role-tracking for user data origin tracing.
10. **Minor:** Heavy reliance on `.mat` files in `engines/` introduces a dependency on external (MATLAB) licenses to reproduce proprietary mathematical bounds.

## Scorecard

| Category | Description | Weight | Score | Evidence / Remediation |
| :--- | :--- | :--- | :--- | :--- |
| Determinism | Random seed setting & float stability | 2x | 8 | **Evidence:** `reproducibility.py` handles seeding well, but float-drift exists. |
| Version Tracking | Dependency & Model config versioning | 2x | 5 | **Evidence:** Unpinned requirements. **Remediation:** Implement `requirements.lock` or `poetry`. |
| Experiment Tracking| MLflow / WandB integration | 1x | 3 | **Evidence:** Missing entirely in parameter sweep modules. |
| Result Reproduction| Bit-exact replication capabilities | 1.5x | 6 | **Evidence:** Tests assert approximations; OS-level differences break pipelines. |

## Refactoring Plan

**48 Hours**
- Audit all file-read calls in `data_io/` to ensure `encoding="utf-8"` is appended, eliminating OS-specific string interpretations.
- Enhance the `reproducibility.py` library to inject execution environment details (Git SHA, active OS, Py version) into resulting data structures.

**2 Weeks**
- Transition the `requirements.txt` methodology to a strictly pinned constraints file (`pip-compile` / `uv`) to lock all transitive dependencies, halting environmental drift.
- Instrument the `multi_param_analysis/` sweeps with basic metadata headers detailing the random seeds, timestamp, and configurations executed.

**6 Weeks**
- Evaluate the adoption of `MLflow` for logging scientific physics experiments and optimizer runs, deprecating direct `.csv` artifact dumping.
- Resolve floating point drift in the MuJoCo simulator bindings by forcing strict timestep quantization.

## Diff Suggestions

**Suggestion 1: Introduce Metadata Headers to Output**
```python
<<<<<<< SEARCH
def save_sweep_results(df, filepath):
    df.to_csv(filepath, index=False)
=======
def save_sweep_results(df, filepath, git_sha, seed):
    import time
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Git SHA: {git_sha}\n")
        f.write(f"# Random Seed: {seed}\n")
        f.write(f"# Timestamp: {time.time()}\n")
        df.to_csv(f, index=False)
>>>>>>> REPLACE
```
