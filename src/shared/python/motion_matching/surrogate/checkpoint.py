"""Persistence helpers for trained surrogate artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from ._normalize import NormalizationStats
from .model import SurrogateConfig, SwingSurrogate
from .train import TrainConfig, TrainedSurrogate, TrainingCurves

_BEST_CHECKPOINT = "best.pt"
_LAST_CHECKPOINT = "last.pt"
_CONFIG_JSON = "config.json"
_METRICS_JSON = "surrogate_v1_metrics.json"
_NORM_STATS_NPZ = "norm_stats.npz"


@dataclass(frozen=True)
class SurrogateArtifactPaths:
    """Filesystem paths written by :func:`save_trained_surrogate`."""

    output_dir: Path
    best_checkpoint: Path
    last_checkpoint: Path
    config_json: Path
    metrics_json: Path
    norm_stats_npz: Path


def save_trained_surrogate(
    bundle: TrainedSurrogate,
    output_dir: str | Path,
    *,
    git_commit: str = "unknown",
) -> SurrogateArtifactPaths:
    """Persist a trained surrogate bundle and companion metadata."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = SurrogateArtifactPaths(
        output_dir=out_dir,
        best_checkpoint=out_dir / _BEST_CHECKPOINT,
        last_checkpoint=out_dir / _LAST_CHECKPOINT,
        config_json=out_dir / _CONFIG_JSON,
        metrics_json=out_dir / _METRICS_JSON,
        norm_stats_npz=out_dir / _NORM_STATS_NPZ,
    )

    checkpoint_payload = {
        "surrogate_config": asdict(bundle.config),
        "train_config": asdict(bundle.train_config),
        "joint_names": list(bundle.joint_names),
        "seq_len": bundle.seq_len,
        "final_val_loss": bundle.final_val_loss,
        "curves": asdict(bundle.curves),
        "git_commit": git_commit,
        "model_state_dict": bundle.model.state_dict(),
        "norm_stats": _norm_stats_payload(bundle.norm_stats),
    }
    torch.save(checkpoint_payload, paths.best_checkpoint)
    torch.save(checkpoint_payload, paths.last_checkpoint)

    np.savez(paths.norm_stats_npz, **_norm_stats_payload(bundle.norm_stats))
    paths.config_json.write_text(
        json.dumps(
            {
                "git_commit": git_commit,
                "surrogate": asdict(bundle.config),
                "train": asdict(bundle.train_config),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    paths.metrics_json.write_text(
        json.dumps(
            {
                "best_checkpoint": str(paths.best_checkpoint),
                "final_val_loss": _json_safe_float(bundle.final_val_loss),
                "git_commit": git_commit,
                "joint_names": list(bundle.joint_names),
                "seq_len": bundle.seq_len,
                "train_loss": [_json_safe_float(v) for v in bundle.curves.train_loss],
                "val_clubhead_rmse_m": [
                    _json_safe_float(v) for v in bundle.curves.val_clubhead_rmse_m
                ],
                "val_loss": [_json_safe_float(v) for v in bundle.curves.val_loss],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return paths


def load_trained_surrogate(checkpoint_path: str | Path) -> TrainedSurrogate:
    """Reload a :class:`TrainedSurrogate` bundle from disk."""
    path = Path(checkpoint_path)
    payload = torch.load(path, map_location="cpu", weights_only=False)
    config = SurrogateConfig(**payload["surrogate_config"])
    model = SwingSurrogate(config)
    model.load_state_dict(payload["model_state_dict"])
    model.eval()

    train_config = TrainConfig(**payload["train_config"])
    curves = TrainingCurves(**payload.get("curves", {}))
    norm_stats = _load_norm_stats(path, payload.get("norm_stats"))
    return TrainedSurrogate(
        model=model,
        config=config,
        train_config=train_config,
        norm_stats=norm_stats,
        curves=curves,
        joint_names=list(payload["joint_names"]),
        seq_len=int(payload["seq_len"]),
        final_val_loss=float(payload["final_val_loss"]),
    )


def _norm_stats_payload(stats: NormalizationStats) -> dict[str, np.ndarray]:
    return {
        "coeffs_mean": np.asarray(stats.coeffs_mean),
        "coeffs_std": np.asarray(stats.coeffs_std),
        "butt_mean": np.asarray(stats.butt_mean),
        "butt_std": np.asarray(stats.butt_std),
        "clubhead_mean": np.asarray(stats.clubhead_mean),
        "clubhead_std": np.asarray(stats.clubhead_std),
    }


def _json_safe_float(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def _load_norm_stats(
    checkpoint_path: Path,
    payload: Any,
) -> NormalizationStats:
    if payload is not None:
        return NormalizationStats(**payload)
    npz_path = checkpoint_path.with_name(_NORM_STATS_NPZ)
    with np.load(npz_path) as data:
        return NormalizationStats(
            coeffs_mean=data["coeffs_mean"],
            coeffs_std=data["coeffs_std"],
            butt_mean=data["butt_mean"],
            butt_std=data["butt_std"],
            clubhead_mean=data["clubhead_mean"],
            clubhead_std=data["clubhead_std"],
        )
