"""Tests for saving and loading trained surrogate artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
from src.shared.python.motion_matching.dataset import (
    load_sweep_dataset,
    make_synthetic_sweep,
)
from src.shared.python.motion_matching.surrogate import (
    TrainConfig,
    load_trained_surrogate,
    save_trained_surrogate,
    train_surrogate,
)
from src.shared.python.motion_matching.surrogate._normalize import zscore_coeffs


def _make_dataset(
    tmp_path: Path,
    *,
    n_trials: int = 4,
    n_joints: int = 2,
    n_timesteps: int = 8,
    seed: int = 0,
):
    folder = make_synthetic_sweep(
        tmp_path / f"ds_{seed}",
        n_trials=n_trials,
        n_joints=n_joints,
        n_timesteps=n_timesteps,
        seed=seed,
    )
    return load_sweep_dataset(folder, lazy=False)


@pytest.mark.unit
def test_save_and_load_trained_surrogate_round_trip(tmp_path: Path) -> None:
    """Saved checkpoints reload into an equivalent TrainedSurrogate bundle."""
    dataset = _make_dataset(tmp_path)
    bundle = train_surrogate(
        dataset,
        TrainConfig(
            n_epochs=1,
            batch_size=2,
            val_fraction=0.2,
            test_fraction=0.0,
            use_amp=False,
        ),
    )

    paths = save_trained_surrogate(
        bundle,
        tmp_path / "artifacts",
        git_commit="deadbeef",
    )

    reloaded = load_trained_surrogate(paths.best_checkpoint)
    coeffs = torch.zeros(1, bundle.config.coeff_dim)

    original_pred = bundle.model(zscore_coeffs(coeffs, bundle.norm_stats))
    reloaded_pred = reloaded.model(zscore_coeffs(coeffs, reloaded.norm_stats))

    assert paths.best_checkpoint.exists()
    assert paths.last_checkpoint.exists()
    assert paths.config_json.exists()
    assert paths.metrics_json.exists()
    assert paths.norm_stats_npz.exists()
    assert reloaded.config == bundle.config
    assert reloaded.joint_names == bundle.joint_names
    assert reloaded.seq_len == bundle.seq_len
    np.testing.assert_allclose(
        reloaded.norm_stats.coeffs_mean, bundle.norm_stats.coeffs_mean
    )
    np.testing.assert_allclose(
        reloaded.norm_stats.coeffs_std, bundle.norm_stats.coeffs_std
    )
    torch.testing.assert_close(original_pred.butt, reloaded_pred.butt)
    torch.testing.assert_close(original_pred.clubhead, reloaded_pred.clubhead)
    torch.testing.assert_close(original_pred.club_quat, reloaded_pred.club_quat)


@pytest.mark.unit
def test_saved_metrics_json_contains_training_summary(tmp_path: Path) -> None:
    """Artifact metadata is persisted in simple JSON files for downstream tools."""
    dataset = _make_dataset(tmp_path, seed=1)
    bundle = train_surrogate(
        dataset,
        TrainConfig(
            n_epochs=1,
            batch_size=2,
            val_fraction=0.2,
            test_fraction=0.0,
            use_amp=False,
        ),
    )

    paths = save_trained_surrogate(
        bundle,
        tmp_path / "artifacts",
        git_commit="cafebabe",
    )

    config_payload = json.loads(paths.config_json.read_text(encoding="utf-8"))
    metrics_payload = json.loads(paths.metrics_json.read_text(encoding="utf-8"))

    assert config_payload["git_commit"] == "cafebabe"
    assert config_payload["surrogate"]["seq_len"] == bundle.seq_len
    assert config_payload["surrogate"]["n_joints"] == len(bundle.joint_names)
    assert metrics_payload["joint_names"] == bundle.joint_names
    assert metrics_payload["seq_len"] == bundle.seq_len
    if metrics_payload["final_val_loss"] is None:
        assert np.isnan(bundle.final_val_loss)
    else:
        assert metrics_payload["final_val_loss"] == pytest.approx(bundle.final_val_loss)
    assert metrics_payload["best_checkpoint"].endswith("best.pt")
