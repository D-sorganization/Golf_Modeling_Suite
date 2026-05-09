"""Command-line entry point for the motion-capture pipeline.

Run ``python -m src.shared.python.motion_pipeline --help`` to see the
available subcommands. The entry point is intentionally minimal: it
dispatches into :class:`MotionPipeline` from :mod:`orchestrator` and
serialises the resulting :class:`MotionMatchingResult` to JSON.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from collections.abc import Sequence

from .orchestrator import AdapterOverride, MotionPipeline, PipelineConfig

logger = logging.getLogger("motion_pipeline.cli")

_KNOWN_ENGINES = ("mujoco", "drake", "pinocchio", "opensim")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.shared.python.motion_pipeline",
        description=(
            "Motion-capture pipeline CLI. Runs adapter -> preprocessing -> "
            "scaling -> IK -> motion-matching for a single input file."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser(
        "run",
        help="Run the full pipeline on an input file.",
        description=(
            "Run the full motion pipeline on INPUT and write a JSON result "
            "to --output. Replaces the (never-shipped) extract_frames / "
            "pose_estimation / lift_3d / retarget / inverse_kinematics "
            "module-style commands once advertised in the README."
        ),
    )
    run_p.add_argument("input", type=Path, help="Path to a mocap source file.")
    run_p.add_argument(
        "--engine",
        choices=_KNOWN_ENGINES,
        default="mujoco",
        help="IK and motion-matching backend (default: mujoco).",
    )
    run_p.add_argument(
        "--source-format",
        default=None,
        help="Adapter format hint (c3d, trc, bvh, csv, json...). "
        "Auto-detected from extension when omitted.",
    )
    run_p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the JSON result here. Defaults to stdout.",
    )
    run_p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable INFO-level logging.",
    )
    return parser


def _infer_format(path: Path, override: str | None) -> str:
    if override:
        return override
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "auto"


def _run(args: argparse.Namespace) -> int:
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    src: Path = args.input
    if not src.exists():
        sys.stderr.write(f"error: input file does not exist: {src}\n")
        return 2
    if args.engine not in _KNOWN_ENGINES:
        # argparse already enforces this, defensive check kept for clarity.
        sys.stderr.write(f"error: unknown engine: {args.engine}\n")
        return 2

    fmt = _infer_format(src, args.source_format)
    config = PipelineConfig(
        adapter=AdapterOverride(format=fmt),
        ik_backend=args.engine,
        matching_backend=args.engine,
    )
    pipeline = MotionPipeline(config)
    try:
        result = pipeline.run(src)
    except (RuntimeError, ValueError) as e:
        sys.stderr.write(f"error: pipeline failed: {e}\n")
        return 1

    payload = {
        "success": getattr(result, "success", True),
        "request_id": getattr(result, "request_id", None),
        "result": result.model_dump() if hasattr(result, "model_dump") else None,
        "audit_log": pipeline.get_audit_log()
        if hasattr(pipeline, "get_audit_log")
        else [],
    }
    text = json.dumps(payload, indent=2, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
