"""Standardized error response envelope for the API.

All 4xx error handlers should return this shape so that clients can
parse errors uniformly. See :func:`validation_exception_handler` in
:mod:`src.api.server` for the global 422 handler.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by API error handlers.

    Attributes:
        detail: Human readable description of the error.
        code: Optional machine readable error code (e.g. ``"validation_error"``).
        errors: Optional list of structured field-level errors. Useful for
            422 responses where we want to surface which fields failed
            validation without dumping the raw Pydantic envelope.
    """

    detail: str = Field(..., description="Human readable description of the error.")
    code: str | None = Field(
        default=None,
        description="Optional machine readable error code.",
    )
    errors: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional list of field-level error details.",
    )
