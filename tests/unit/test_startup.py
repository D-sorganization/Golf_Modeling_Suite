"""Unit tests for the AsyncStartupWorker."""

from unittest.mock import MagicMock, patch

from src.launchers.startup import AsyncStartupWorker


def test_async_startup_worker_docker_missing(qtbot):
    worker = AsyncStartupWorker(MagicMock())

    with patch("src.launchers.startup.secure_run") as mock_run:
        # Simulate Docker missing exception
        mock_run.side_effect = Exception("Docker not found")

        # Mock other checks so they don't fail or take long
        # Mock other checks so they don't fail or take long
        with (
            patch(
                "src.shared.python.config.model_registry.ModelRegistry",
                return_value=MagicMock(),
            ),
            patch(
                "src.shared.python.engine_core.engine_manager.EngineManager",
                return_value=MagicMock(),
            ),
        ):
            worker.run()

        # Verify it handled it and set docker_available to False
        assert worker.results.docker_available is False


def test_async_startup_worker_error_signal(qtbot):
    worker = AsyncStartupWorker(MagicMock())
    error_spy = MagicMock()
    worker.error_signal.connect(error_spy)

    with patch(
        "src.shared.python.config.model_registry.ModelRegistry",
        side_effect=Exception("Critical Failure"),
    ):
        worker.run()

    error_spy.assert_called_once_with("Critical Failure")
