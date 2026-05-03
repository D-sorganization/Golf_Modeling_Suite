from __future__ import annotations

from fastapi.testclient import TestClient


def test_local_launcher_serves_bundled_ui_dist(
    monkeypatch,
    tmp_path,
) -> None:
    """The launcher must serve the Vite bundle from ``ui/dist``."""
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text(
        "<!doctype html><div id='root'>UpstreamDrift UI</div>",
        encoding="utf-8",
    )
    (assets_dir / "app.js").write_text(
        "console.log('upstream-drift')", encoding="utf-8"
    )
    monkeypatch.setenv("GOLF_UI_DIST", str(dist_dir))

    from src.api.local_server import create_local_app

    client = TestClient(create_local_app())

    response = client.get("/")
    assert response.status_code == 200
    assert "UpstreamDrift UI" in response.text

    asset_response = client.get("/assets/app.js")
    assert asset_response.status_code == 200
    assert "upstream-drift" in asset_response.text
