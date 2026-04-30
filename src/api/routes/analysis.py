"""Analysis routes.

Provides endpoints for biomechanical analysis.
All dependencies are injected via FastAPI's Depends() mechanism.
No module-level mutable state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.shared.python.core.contracts import precondition

from ..dependencies import get_analysis_service, get_logger
from ..models.requests import AnalysisRequest
from ..models.responses import AnalysisResponse

if TYPE_CHECKING:
    from ..services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])

# Use shared limiter - registered with app.state in server.py.
# Per-IP rate limit for the synchronous biomechanics analysis endpoint
# (Issue #3508). Conservative since analysis runs are CPU-intensive.
limiter = Limiter(key_func=get_remote_address)
ANALYZE_RATE_LIMIT = "20/minute"


@router.post("/analyze/biomechanics", response_model=AnalysisResponse)
@limiter.limit(ANALYZE_RATE_LIMIT)
@precondition(
    lambda request, analysis_request=None, service=None, logger=None: (
        analysis_request is not None
    ),
    "Analysis request must not be None",
)
async def analyze_biomechanics(
    request: Request,
    analysis_request: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
    logger: Any = Depends(get_logger),
) -> AnalysisResponse:
    """Perform biomechanical analysis on simulation data (rate-limited per IP).

    Args:
        request: FastAPI request object (used by the rate limiter).
        analysis_request: Analysis parameters.
        service: Injected analysis service.
        logger: Injected logger.

    Returns:
        Analysis results.

    Raises:
        HTTPException: On analysis failure.
    """
    try:
        result = await service.analyze_biomechanics(analysis_request)
        return result
    except (RuntimeError, TypeError, AttributeError) as exc:
        if logger:
            logger.error("Analysis error: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Analysis failed: {str(exc)}"
        ) from exc
