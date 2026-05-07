"""Thin training entrypoint for the Option 2 surrogate."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

from src.shared.python.logging_pkg.logging_config import get_logger
from src.shared.python.motion_matching.dataset import load_sweep_dataset
from src.shared.python.motion_matching.surrogate import (
    TrainConfig,
    save_trained_surrogate,
    train_surrogate,
)

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for training and persisting Option 2 artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--n-epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3.0e-4)
    parser.add_argument("--weight-decay", type=float, default=1.0e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0xC0FFEE)
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--test-fraction", type=float, default=0.1)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--disable-amp",
        action="store_true",
        help="Disable mixed precision even when CUDA is available.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Train a surrogate from a sweep dataset and persist its artifacts."""
    args = build_parser().parse_args(argv)
    logger.info("Loading sweep dataset from %s", args.dataset_path)
    dataset = load_sweep_dataset(args.dataset_path, lazy=False)
    bundle = train_surrogate(
        dataset,
        TrainConfig(
            n_epochs=args.n_epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            weight_decay=args.weight_decay,
            grad_clip=args.grad_clip,
            seed=args.seed,
            val_fraction=args.val_fraction,
            test_fraction=args.test_fraction,
            use_amp=not args.disable_amp,
            device=args.device,
        ),
    )
    paths = save_trained_surrogate(
        bundle,
        args.output_dir,
        git_commit=_git_commit_or_unknown(),
    )
    logger.info("Persisted surrogate artifacts to %s", paths.output_dir)
    return 0


def _git_commit_or_unknown() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
