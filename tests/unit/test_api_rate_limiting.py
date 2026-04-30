"""Rate-limiting wiring tests for the API.

These tests assert that the slowapi limiter is wired correctly and that
once the per-IP budget is exhausted, the next request returns HTTP 429.
We use a tiny isolated FastAPI app rather than booting the real
``src.api.server`` because the latter pulls in heavy physics
dependencies (mujoco, drake, etc.) and a database, which are not
desirable for a unit test.

Note: this module deliberately omits ``from __future__ import annotations``
because FastAPI's parameter resolver inspects runtime annotations to
detect ``Request``. With PEP 563 string annotations the lookup falls
back to treating ``request`` as a query parameter and the route would
422 instead of running.

Issue: https://github.com/.../issues/3508
"""

from typing import Any

import pytest

pytestmark = pytest.mark.unit


def _build_isolated_app(rate: str = "3/minute"):
    """Build a tiny FastAPI app wired to slowapi the same way as src.api.server.

    Returns a tuple of ``(app, endpoint_path)``.
    """
    from fastapi import FastAPI, Request
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.post("/simulate")
    @limiter.limit(rate)
    async def simulate(request: Request) -> Any:
        return {"status": "ok"}

    return app, "/simulate"


def test_rate_limiter_returns_429_after_budget_exhausted() -> None:
    """Hitting an endpoint past its limit should return 429."""
    from fastapi.testclient import TestClient

    app, endpoint = _build_isolated_app(rate="3/minute")
    client = TestClient(app)

    successes = 0
    last_status = None
    last_body: str | None = None
    for _ in range(10):
        resp = client.post(endpoint)
        last_status = resp.status_code
        last_body = resp.text
        if resp.status_code == 200:
            successes += 1
        elif resp.status_code == 429:
            break

    assert successes == 3, (
        "Expected exactly 3 successful requests before throttling, "
        f"got {successes} (last status={last_status}, body={last_body!r})"
    )
    assert last_status == 429, (
        f"Expected the next request after the budget to be 429, got {last_status}"
    )


def test_rate_limiter_429_response_has_detail() -> None:
    """The default slowapi 429 response includes a parseable error body."""
    from fastapi.testclient import TestClient

    app, endpoint = _build_isolated_app(rate="1/minute")
    client = TestClient(app)

    # Burn the single allowed request
    first = client.post(endpoint)
    assert first.status_code == 200

    # Next request must trip the limiter
    second = client.post(endpoint)
    assert second.status_code == 429
    # slowapi's default body is text-y; the important contract is the status
    # code + a non-empty body so clients know they were throttled.
    assert second.text


def test_simulation_route_uses_shared_limiter() -> None:
    """The shipped ``simulation`` router must declare a slowapi limiter.

    This is a structural assertion: it locks in that we did not regress
    the rate-limit wiring on the real /simulate endpoint, without needing
    to import the full FastAPI app (which has heavy deps).
    """
    from src.api.routes import simulation

    assert hasattr(simulation, "limiter"), (
        "simulation route module must expose a `limiter` for /simulate"
    )
    assert simulation.SIMULATE_RATE_LIMIT, "SIMULATE_RATE_LIMIT must be non-empty"


def test_analysis_route_uses_shared_limiter() -> None:
    """The shipped ``analysis`` router must declare a slowapi limiter."""
    from src.api.routes import analysis

    assert hasattr(analysis, "limiter"), (
        "analysis route module must expose a `limiter` for /analyze/biomechanics"
    )
    assert analysis.ANALYZE_RATE_LIMIT, "ANALYZE_RATE_LIMIT must be non-empty"


def test_dataset_generate_route_uses_shared_limiter() -> None:
    """The shipped ``dataset`` router must declare a slowapi limiter."""
    from src.api.routes import dataset

    assert hasattr(dataset, "limiter"), (
        "dataset route module must expose a `limiter` for /dataset/generate"
    )
    assert dataset.DATASET_GENERATE_RATE_LIMIT, (
        "DATASET_GENERATE_RATE_LIMIT must be non-empty"
    )


def test_error_response_schema_is_importable() -> None:
    """The standardized error envelope is importable and has the expected fields."""
    from src.api.schemas.errors import ErrorResponse

    err = ErrorResponse(detail="bad", code="validation_error")
    dumped = err.model_dump()
    assert dumped["detail"] == "bad"
    assert dumped["code"] == "validation_error"
    assert dumped["errors"] is None
