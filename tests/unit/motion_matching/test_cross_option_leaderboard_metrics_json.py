"""Metrics JSON contract tests for the cross-option leaderboard CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_cross_option_leaderboard.py"


def _load_leaderboard_module():
    spec = importlib.util.spec_from_file_location(
        "run_cross_option_leaderboard", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _reject_nonstandard_json_constant(value: str) -> None:
    raise AssertionError(f"metrics JSON used non-standard constant {value!r}")


def test_metrics_json_uses_null_for_no_success_best_rmse(tmp_path, monkeypatch):
    """No successful fit should not serialize the infinite best-RMSE sentinel."""
    module = _load_leaderboard_module()
    summary = module.LeaderboardSummary(
        total_fits=1,
        failed_fits=1,
        best_grip_rmse_mm=float("inf"),
    )

    monkeypatch.setattr(module, "run_all", lambda _args: (summary, {}))

    metrics_path = tmp_path / "metrics.json"
    exit_code = module.main(
        [
            "--results-dir",
            str(tmp_path / "results"),
            "--leaderboard-path",
            str(tmp_path / "LEADERBOARD.md"),
            "--report-path",
            str(tmp_path / "REPORT.md"),
            "--metrics-path",
            str(metrics_path),
            "--no-visualizations",
        ]
    )

    assert exit_code == 0
    metrics_text = metrics_path.read_text(encoding="utf-8")
    assert "Infinity" not in metrics_text
    metrics = json.loads(metrics_text, parse_constant=_reject_nonstandard_json_constant)
    assert metrics["best_grip_rmse_mm"] is None
