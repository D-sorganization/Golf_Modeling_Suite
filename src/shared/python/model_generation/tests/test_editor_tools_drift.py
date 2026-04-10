"""Drift guard for the editor leaf modules synchronized with Tools.

The baseline hashes were captured from the matching files in the sibling
Tools repository and should only change when that upstream source changes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]

TOOLS_BASELINE_HASHES: dict[str, str] = {
    "src/shared/python/model_generation/editor/__init__.py": "64b21248d28d9a9a380cbbb4e8a6f80fa44ce241bbd37d31156c00bd9c735587",
    "src/shared/python/model_generation/editor/editor_types.py": "ce04d69d6f0ed3fee8adcfadbd302c56a7cbeb37ea147ef8b13fd35b4019a390",
    "src/shared/python/model_generation/editor/text_editor_diff_mixin.py": "f04647e3bff584a2cfc576dfc239e4352564c8193f65ca17aa6a46b7d9d9f5c9",
}


@pytest.mark.parametrize(
    ("relative_path", "expected_sha256"),
    sorted(TOOLS_BASELINE_HASHES.items()),
)
def test_editor_leaf_modules_match_tools_baseline(
    relative_path: str,
    expected_sha256: str,
) -> None:
    """Verify the selected leaf modules still match the Tools baseline."""
    file_path = REPO_ROOT / relative_path
    actual_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
    assert actual_sha256 == expected_sha256, relative_path
