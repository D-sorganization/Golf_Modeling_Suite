"""Offscreen composition workspace tests for issue #7207."""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtWidgets import QApplication

from src.tools.model_explorer.composition_workspace import CompositionWorkspace
from src.tools.model_explorer.frankenstein_editor.model import URDFModel

pytestmark = [pytest.mark.unit]

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


class FakeLibrary:
    def __init__(self, target_path: Path, source_path: Path) -> None:
        self._models: dict[tuple[str, str], dict[str, Any]] = {
            (
                "discovered",
                "target_humanoid",
            ): {
                "name": "Simple Humanoid",
                "description": "Target human model with a hand mount.",
                "path": str(target_path),
                "type": "urdf",
                "config_key": "target_humanoid",
                "attachment_points": [
                    {
                        "name": "right hand mount",
                        "link_name": "right_hand",
                        "role": "tool_mount",
                        "interface_frame": {
                            "xyz": [0.1, 0.2, 0.3],
                            "rpy": [0.0, 0.0, 0.0],
                        },
                    }
                ],
            },
            (
                "sibling",
                "source_arm",
            ): {
                "name": "Simple Arm",
                "description": "Sibling robot arm source model.",
                "path": str(source_path),
                "type": "urdf",
                "repo": "Robot_Models",
                "config_key": "source_arm",
            },
        }

    def list_available_models(self) -> dict[str, Any]:
        return {
            "discovered": [self._models[("discovered", "target_humanoid")]],
            "sibling": [self._models[("sibling", "source_arm")]],
        }

    def get_model_info(self, category: str, key: str) -> dict[str, Any] | None:
        return self._models.get((category, key))


def test_workspace_composes_library_models_and_exports(
    qapp: QApplication, tmp_path: Path
) -> None:
    del qapp
    target_path = tmp_path / "human.urdf"
    source_path = tmp_path / "arm.urdf"
    target_path.write_text(
        """<robot name="human">
  <link name="pelvis"/>
  <link name="right_hand"/>
  <joint name="pelvis_to_hand" type="fixed">
    <parent link="pelvis"/>
    <child link="right_hand"/>
  </joint>
</robot>""",
        encoding="utf-8",
    )
    source_path.write_text(
        """<robot name="arm">
  <link name="base"/>
  <link name="tool"/>
  <joint name="base_to_tool" type="fixed">
    <parent link="base"/>
    <child link="tool"/>
  </joint>
</robot>""",
        encoding="utf-8",
    )
    target_path.with_suffix(".attachments.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "attachment_points": [
                    {
                        "name": "right hand mount",
                        "link_name": "right_hand",
                        "role": "tool_mount",
                        "interface_frame": {
                            "xyz": [0.1, 0.2, 0.3],
                            "rpy": [0.0, 0.0, 0.0],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    workspace = CompositionWorkspace(library=FakeLibrary(target_path, source_path))
    assert workspace.library_tree.dragEnabled()
    assert workspace.load_source_btn.acceptDrops()
    assert workspace.load_working_btn.acceptDrops()

    workspace.select_library_entry("discovered", "target_humanoid")
    current = workspace.library_tree.currentItem()
    assert current is not None
    mime = workspace.library_tree.mimeData([current])
    assert any("upstreamdrift-model-entry" in fmt for fmt in mime.formats())
    assert workspace.load_selected_as_working()
    workspace.select_library_entry("sibling", "source_arm")
    assert workspace.load_selected_as_source()
    assert workspace.attach_source_to_working()

    working = workspace.editor.get_working_model()
    assert working is not None
    assert working.links.keys() >= {"pelvis", "right_hand", "arm_base", "arm_tool"}
    assert workspace.validation_status_label.text() == "Validation passed"

    urdf = workspace.export_working_model("urdf")
    assert urdf is not None
    assert 'link name="arm_tool"' in urdf
    reparsed = URDFModel.from_element(ET.fromstring(urdf))
    assert "arm_base" in reparsed.links

    mjcf = workspace.export_working_model("mjcf")
    assert mjcf is not None
    assert "<mujoco" in mjcf


def test_workspace_rejects_model_entries_without_paths(qapp: QApplication) -> None:
    del qapp

    class MissingPathLibrary:
        def list_available_models(self) -> dict[str, Any]:
            return {"component": [{"config_key": "ball", "name": "Ball"}]}

        def get_model_info(self, category: str, key: str) -> dict[str, Any] | None:
            return (
                {"name": "Ball"} if (category, key) == ("component", "ball") else None
            )

    workspace = CompositionWorkspace(library=MissingPathLibrary())
    workspace.select_library_entry("component", "ball")

    assert not workspace.load_selected_as_source()
    assert "does not expose a file path" in workspace.status_label.text()
