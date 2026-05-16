"""TDD tests for launcher_manifest.json tile coverage.

Verifies that all 9 missing-tile issues are resolved:
  #5512 shot_tracer, #5513 pose_studio, #5515 engine dashboards (3),
  #5516 swing_optimization, #5517 injury_risk, #5518 terrain_api,
  #5521 analysis_tools_api, #5522 chat_sidekick, #5523 motion_pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

MANIFEST_PATH = Path(__file__).parents[2] / "src" / "config" / "launcher_manifest.json"

EXPECTED_TILE_IDS = [
    "shot_tracer",  # #5512 — MultiModelShotTracerWindow
    "pose_studio",  # #5513 — PoseStudioApp (already in models.yaml, must be in manifest)
    "drake_dashboard",  # #5515 — Drake engine dashboard
    "mujoco_dashboard",  # #5515 — MuJoCo engine dashboard
    "pinocchio_dashboard",  # #5515 — Pinocchio engine dashboard
    "swing_optimization",  # #5516 — Swing Optimization UI entry
    "injury_risk",  # #5517 — Injury Risk Analysis
    "terrain_api",  # #5518 — Terrain REST API tile
    "analysis_tools_api",  # #5521 — Analysis Tools API tile
    "chat_sidekick",  # #5522 — Chat / AI Sidekick
    "motion_pipeline",  # #5523 — Motion Pipeline tile
]


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the launcher manifest JSON."""
    assert MANIFEST_PATH.exists(), f"Manifest not found: {MANIFEST_PATH}"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tile_ids(manifest: dict) -> set[str]:
    """Extract the set of all tile IDs from the manifest."""
    return {tile["id"] for tile in manifest.get("tiles", [])}


@pytest.mark.parametrize("tile_id", EXPECTED_TILE_IDS)
def test_tile_exists_in_manifest(tile_id: str, tile_ids: set[str]) -> None:
    """Each expected tile ID must be present in launcher_manifest.json."""
    assert tile_id in tile_ids, (
        f"Tile '{tile_id}' not found in launcher_manifest.json. "
        f"Present tiles: {sorted(tile_ids)}"
    )


@pytest.mark.parametrize("tile_id", EXPECTED_TILE_IDS)
def test_tile_has_required_fields(tile_id: str, manifest: dict) -> None:
    """Each new tile must have the required fields: id, name, description, category, status."""
    tiles_by_id = {tile["id"]: tile for tile in manifest.get("tiles", [])}
    if tile_id not in tiles_by_id:
        pytest.skip(f"Tile '{tile_id}' not present — skipping field check")
    tile = tiles_by_id[tile_id]
    for field in ("id", "name", "description", "category", "status"):
        assert field in tile, f"Tile '{tile_id}' missing required field '{field}'"


def test_all_tiles_have_unique_ids(manifest: dict) -> None:
    """No duplicate IDs in the manifest."""
    ids = [tile["id"] for tile in manifest.get("tiles", [])]
    assert len(ids) == len(set(ids)), f"Duplicate tile IDs: {ids}"


@pytest.mark.parametrize(
    "tile_id,expected_category",
    [
        ("shot_tracer", "simulation"),
        ("pose_studio", "tool"),
        ("drake_dashboard", "physics_engine"),
        ("mujoco_dashboard", "physics_engine"),
        ("pinocchio_dashboard", "physics_engine"),
        ("swing_optimization", "biomechanics"),
        ("injury_risk", "biomechanics"),
        ("terrain_api", "tool"),
        ("analysis_tools_api", "tool"),
        ("chat_sidekick", "tool"),
        ("motion_pipeline", "motion_matching"),
    ],
)
def test_tile_category(tile_id: str, expected_category: str, manifest: dict) -> None:
    """Each new tile must have the correct category."""
    tiles_by_id = {tile["id"]: tile for tile in manifest.get("tiles", [])}
    if tile_id not in tiles_by_id:
        pytest.skip(f"Tile '{tile_id}' not present — skipping category check")
    assert tiles_by_id[tile_id]["category"] == expected_category, (
        f"Tile '{tile_id}' has category '{tiles_by_id[tile_id]['category']}', "
        f"expected '{expected_category}'"
    )
