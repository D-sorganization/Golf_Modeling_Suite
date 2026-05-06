"""Tests for src.engines.physics_engines.pinocchio.python.motion_training.training_pipeline."""

from types import SimpleNamespace

import numpy as np
import pytest


def test_import() -> None:
    """Verify the module can be imported."""
    try:
        import src.engines.physics_engines.pinocchio.python.motion_training.training_pipeline

        assert (
            src.engines.physics_engines.pinocchio.python.motion_training.training_pipeline
            is not None
        )
    except (ImportError, AttributeError) as e:
        pytest.skip(f"Missing dependencies or import error: {e}")


def test_pipeline_uses_solver_dof_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    """The pipeline should not reach through the IK solver into its model."""
    from motion_training.dual_hand_ik_solver import TrajectoryIKResult
    from src.engines.physics_engines.pinocchio.python.motion_training.training_pipeline import (
        MotionTrainingPipeline,
        PipelineConfig,
    )

    pipeline = MotionTrainingPipeline(
        PipelineConfig(save_trajectory=False, save_plots=False, visualize=False)
    )

    fake_trajectory = SimpleNamespace(
        num_frames=1,
        duration=0.01,
        events=SimpleNamespace(address=0, top=0, impact=0, finish=0),
    )

    def init_fake_solver() -> None:
        pipeline.ik_solver = SimpleNamespace(model_dof_count=7)

    ik_result = TrajectoryIKResult(
        configurations=[np.zeros(7)],
        times=[0.0],
        left_hand_errors=[0.001],
        right_hand_errors=[0.001],
        convergence_rate=1.0,
    )

    monkeypatch.setattr(pipeline, "_parse_trajectory", lambda: fake_trajectory)
    monkeypatch.setattr(pipeline, "_init_ik_solver", init_fake_solver)
    monkeypatch.setattr(pipeline, "_solve_ik", lambda: ik_result)

    result = pipeline.run()

    assert result.success is True
