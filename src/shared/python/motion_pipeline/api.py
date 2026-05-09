"""
FastAPI API endpoint for MotionPipeline.

Part of issue #4569. Provides REST API for motion capture pipeline.

Usage:
    from src.shared.python.motion_pipeline.api import app
    # or
    from src.shared.python.motion_pipeline.api import create_app
    app = create_app()

    # Run with: uvicorn src.shared.python.motion_pipeline.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from .contracts import MotionMatchingResult
from .orchestrator import AdapterOverride, MotionPipeline, PipelineConfig, Stage

logger = logging.getLogger(__name__)


# =============================================================================
# API Models
# =============================================================================


class PipelineRequest(BaseModel):
    """Pydantic-validated request model for motion pipeline API.

    Matches the PipelineConfig from orchestrator with additional file
    handling fields. Used as the JSON body for the ``/run`` endpoint.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Adapter configuration
    source_format: str = Field(
        ..., description="Source format (c3d, trc, bvh, json, mat, fbx)"
    )
    adapter_options: dict[str, Any] = Field(
        default_factory=dict, description="Format-specific adapter options"
    )

    # Preprocessing steps
    preprocessing: list[dict[str, Any]] = Field(
        default_factory=list, description="Ordered list of preprocessing steps"
    )

    # Scaling configuration
    scaling: dict[str, Any] = Field(
        default_factory=dict, description="Scaling marker map and options"
    )

    # Backend selection
    ik_backend: str = Field(
        default="mujoco", description="IK backend (mujoco, drake, pinocchio, opensim)"
    )
    matching_backend: str = Field(
        default="mujoco", description="Motion matching backend"
    )

    # Cost weights
    cost_weights: dict[str, float] = Field(
        default_factory=dict, description="Cost function weights"
    )

    def to_pipeline_config(self) -> PipelineConfig:
        """Convert this API request to an orchestrator PipelineConfig."""
        return PipelineConfig(
            adapter=AdapterOverride(
                format=self.source_format, options=self.adapter_options
            ),
            preprocessing=[
                {
                    "name": step.get("name", ""),
                    "enabled": step.get("enabled", True),
                    "params": step.get("params", {}),
                }
                for step in self.preprocessing
            ],
            scaling=self.scaling,
            ik_backend=self.ik_backend,
            matching_backend=self.matching_backend,
            cost_weights=self.cost_weights,
        )


class PipelineResponse(BaseModel):
    """Response model for motion pipeline API.

    Wraps MotionMatchingResult with additional metadata.
    """

    request_id: str = Field(..., description="Associated request identifier")
    success: bool = Field(..., description="Whether processing succeeded")
    result: dict[str, Any] | None = Field(
        default=None, description="Matched trajectory and metrics (if success)"
    )
    error: str | None = Field(default=None, description="Error message (if failed)")
    audit_log: list[dict[str, Any]] = Field(
        default_factory=list, description="Per-stage audit log for provenance"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @classmethod
    def from_result(
        cls, result: MotionMatchingResult, audit_log: list[dict[str, Any]]
    ) -> PipelineResponse:
        """Create response from MotionMatchingResult."""
        return cls(
            request_id=result.request_id,
            success=result.success,
            result=result.model_dump() if result.success else None,
            error=result.message if not result.success else None,
            audit_log=audit_log,
            metadata=result.metadata,
        )

    @classmethod
    def from_error(cls, request_id: str, error: str) -> PipelineResponse:
        """Create error response."""
        return cls(request_id=request_id, success=False, error=error, audit_log=[])


# =============================================================================
# Internal helpers
# =============================================================================


def _save_upload_to_temp(file: UploadFile, content: bytes) -> Path:
    """Persist an uploaded file to a temp path and return it."""
    suffix = Path(file.filename).suffix if file.filename else ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        return Path(tmp.name)


def _run_pipeline_sync(
    config: PipelineConfig, tmp_path: Path, request_id: str
) -> PipelineResponse:
    """Run the orchestrator and convert exceptions into a typed response."""
    pipeline = MotionPipeline(config)

    def log_hook(payload: Any) -> None:
        logger.info("Request %s: stage %s completed", request_id, payload.stage.value)

    for stage in Stage:
        pipeline.add_hook(stage, log_hook)

    try:
        result = pipeline.run(tmp_path)
        audit_log = pipeline.get_audit_log()
        return PipelineResponse.from_result(result, audit_log)
    except RuntimeError as e:
        logger.error("Request %s: pipeline error: %s", request_id, e)
        return PipelineResponse.from_error(request_id, str(e))
    except Exception as e:  # noqa: BLE001 - API boundary, all errors must surface as JSON
        logger.exception("Request %s: unexpected error", request_id)
        return PipelineResponse.from_error(request_id, f"Internal error: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)


# =============================================================================
# FastAPI Application
# =============================================================================


def create_app() -> FastAPI:
    """Create FastAPI application with motion pipeline endpoints."""
    app = FastAPI(
        title="Motion Capture Pipeline API",
        description="REST API for motion capture processing",
        version="1.0.0",
    )

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.post(
        "/api/v1/motion-pipeline/run",
        response_model=PipelineResponse,
        status_code=status.HTTP_200_OK,
        summary="Run motion pipeline (multipart form)",
        description=(
            "Process motion capture data through the full pipeline:\n"
            "adapter -> preprocessing -> scaling -> IK -> motion-matching.\n\n"
            "Multipart form upload. For full configuration control, use "
            "``/api/v1/motion-pipeline/run-config`` with a JSON body."
        ),
        responses={
            200: {"description": "Processing completed", "model": PipelineResponse},
            400: {"description": "Invalid input or configuration"},
            422: {"description": "Validation error"},
            500: {"description": "Internal server error"},
        },
    )
    async def run_pipeline(
        file: UploadFile = File(..., description="Motion capture file"),
        source_format: str = Form(
            ..., description="Source format (c3d, trc, bvh, ...)"
        ),
        ik_backend: str = Form("mujoco", description="IK backend"),
        matching_backend: str = Form("mujoco", description="Matching backend"),
    ) -> PipelineResponse:
        """Run motion pipeline on an uploaded file using form fields."""
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        logger.info("Received pipeline request %s for %s", request_id, file.filename)

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided",
            )

        content = await file.read()
        tmp_path = _save_upload_to_temp(file, content)

        config = PipelineConfig(
            adapter=AdapterOverride(format=source_format),
            ik_backend=ik_backend,
            matching_backend=matching_backend,
        )
        return _run_pipeline_sync(config, tmp_path, request_id)

    @app.post(
        "/api/v1/motion-pipeline/run-config",
        response_model=PipelineResponse,
        status_code=status.HTTP_200_OK,
        summary="Run motion pipeline with full JSON config",
        description=(
            "Run motion pipeline with full configuration control. "
            "Accepts a JSON body matching ``PipelineRequest``."
        ),
    )
    async def run_pipeline_with_config(
        request: PipelineRequest,
    ) -> PipelineResponse:
        """Run motion pipeline with a full JSON config body.

        For uploads, use ``/api/v1/motion-pipeline/run`` (multipart).
        This endpoint expects the source file to be referenced via
        ``adapter_options['path']``.
        """
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        logger.info("Received config-only pipeline request %s", request_id)

        path_str = request.adapter_options.get("path")
        if not path_str:
            return PipelineResponse.from_error(
                request_id,
                "adapter_options.path is required for /run-config endpoint",
            )
        tmp_path = Path(path_str)
        if not tmp_path.exists():
            return PipelineResponse.from_error(
                request_id, f"Source file does not exist: {tmp_path}"
            )

        return _run_pipeline_sync(request.to_pipeline_config(), tmp_path, request_id)

    return app


# Module-level app for `uvicorn motion_pipeline.api:app` and direct imports.
app = create_app()


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
