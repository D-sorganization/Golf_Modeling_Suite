"""Tests for static-path hardening in local server routes."""

import pytest
from fastapi.testclient import TestClient

local_server = pytest.importorskip("src.api.local_server")


@pytest.fixture
def local_client(monkeypatch, tmp_path):
    """Create a local server client with a minimal temporary UI dist directory."""
    ui_dist = tmp_path / "ui" / "dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html><body>Local UI</body></html>")
    (ui_dist / "safe.txt").write_text("safe")
    nested_dir = ui_dist / "nested"
    nested_dir.mkdir()
    (nested_dir / "safe.txt").write_text("nested")

    monkeypatch.setenv("GOLF_UI_DIST", str(ui_dist))
    local_server._startup_metrics.update(
        {
            "startup_time": None,
            "static_files_mounted": False,
            "ui_path": None,
            "engines_loaded": [],
            "errors": [],
        }
    )

    app = local_server.create_local_app()
    with TestClient(app) as client:
        yield client


def test_spa_rejects_nested_traversal_path(local_client: TestClient) -> None:
    response = local_client.get("/nested/../safe.txt")
    assert response.status_code == 400


def test_spa_allows_nested_file_when_in_bounds(local_client: TestClient) -> None:
    response = local_client.get("/nested/safe.txt")
    assert response.status_code == 200
    assert response.text == "nested"


def test_spa_rejects_encoded_parent_traversal(local_client: TestClient) -> None:
    response = local_client.get("/%2E%2E%2Fsafe.txt")
    assert response.status_code == 400


def test_logo_route_rejects_traversal(local_client: TestClient) -> None:
    response = local_client.get("/api/launcher/logos/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code == 404


def test_logo_route_rejects_windows_path_traversal(local_client: TestClient) -> None:
    response = local_client.get("/api/launcher/logos/..\\secret.svg")
    assert response.status_code == 404
