"""Regression tests for issue #4722: FastAPI registration crash.

Before the fix, ``create_app()`` crashed with::

    AssertionError: non-body parameters must be in path, query, header
    or cookie: source_format

These tests guard the module-level ``app`` symbol, the route surface,
and the request/response schemas.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi.testclient")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.shared.python.motion_pipeline import api as api_module  # noqa: E402


def test_app_module_attr_exists() -> None:
    """``from ...api import app`` must succeed (issue #4722)."""
    assert hasattr(api_module, "app")
    assert isinstance(api_module.app, FastAPI)


def test_create_app_does_not_crash() -> None:
    """``create_app()`` must not raise at registration time."""
    app = api_module.create_app()
    assert isinstance(app, FastAPI)


def test_app_has_expected_routes() -> None:
    paths = {getattr(r, "path", None) for r in api_module.app.routes}
    assert "/health" in paths
    assert "/api/v1/motion-pipeline/run" in paths
    assert "/api/v1/motion-pipeline/run-config" in paths


def test_health_endpoint_returns_200() -> None:
    client = TestClient(api_module.app)
    r = client.get("/health")
    assert r.status_code == 200


def test_run_endpoint_validates_request_body() -> None:
    """Empty multipart body must produce a 422, not a crash."""
    client = TestClient(api_module.app)
    r = client.post("/api/v1/motion-pipeline/run")
    assert r.status_code == 422


def test_run_config_endpoint_validates_request_body() -> None:
    client = TestClient(api_module.app)
    r = client.post("/api/v1/motion-pipeline/run-config", json={})
    assert r.status_code == 422


def test_openapi_schema_advertises_form_fields() -> None:
    """The /run endpoint must expose source_format as a form field."""
    client = TestClient(api_module.app)
    schema = client.get("/openapi.json").json()
    run_post = schema["paths"]["/api/v1/motion-pipeline/run"]["post"]
    body_schema = run_post["requestBody"]["content"]["multipart/form-data"]["schema"]
    # Either inline properties or a $ref to a generated body model
    if "$ref" in body_schema:
        ref = body_schema["$ref"].split("/")[-1]
        body_schema = schema["components"]["schemas"][ref]
    props = body_schema.get("properties", {})
    assert "file" in props
    assert "source_format" in props
