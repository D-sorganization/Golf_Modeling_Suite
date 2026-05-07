"""Tests for the Option 2 training entrypoint."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from src.shared.python.motion_matching.dataset import make_synthetic_sweep

from ._fixtures import repo_root


def _load_train_module():
    script_path = (
        repo_root()
        / "src/engines/Simscape_Multibody_Models/3D_Golf_Model/matlab"
        / "motion_matching/option2_nn_surrogate/train.py"
    )
    spec = importlib.util.spec_from_file_location("option2_train", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Option 2 train module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_option2_train_cli_writes_expected_artifacts(tmp_path: Path) -> None:
    """The CLI should train on a tiny synthetic sweep and persist artifacts."""
    option2_train = _load_train_module()
    dataset_path = make_synthetic_sweep(
        tmp_path / "sweep",
        n_trials=6,
        n_joints=3,
        n_timesteps=12,
        seed=7,
    )
    output_dir = tmp_path / "output"

    exit_code = option2_train.main(
        [
            "--dataset-path",
            str(dataset_path),
            "--output-dir",
            str(output_dir),
            "--n-epochs",
            "1",
            "--batch-size",
            "2",
            "--val-fraction",
            "0.2",
            "--test-fraction",
            "0.0",
            "--disable-amp",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "best.pt").exists()
    assert (output_dir / "last.pt").exists()
    assert (output_dir / "config.json").exists()
    assert (output_dir / "norm_stats.npz").exists()
    assert (output_dir / "surrogate_v1_metrics.json").exists()

    metrics_payload = json.loads(
        (output_dir / "surrogate_v1_metrics.json").read_text(encoding="utf-8")
    )
    assert metrics_payload["seq_len"] == 12
    assert metrics_payload["joint_names"] == ["joint_00", "joint_01", "joint_02"]
