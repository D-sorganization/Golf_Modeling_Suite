"""Unified library-to-composition workspace for the Model Explorer."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET  # stdlib retained for URDF model assembly
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.tools.model_explorer.composition_flow import ExportFormat
from src.tools.model_explorer.attachment_manifest import load_attachment_manifest
from src.tools.model_explorer.frankenstein_editor import FrankensteinEditor
from src.tools.model_explorer.frankenstein_editor.model import URDFModel
from src.tools.model_explorer.library_panel_model import (
    LibraryModelEntry,
    LibraryPanelModel,
)

_ENTRY_MIME_TYPE = "application/x-upstreamdrift-model-entry+json"


class CompositionWorkspace(QWidget):
    """Single-screen model library, composition editor, validation, and export UI."""

    def __init__(self, parent: QWidget | None = None, *, library: Any | None = None):
        """Create a composition workspace from a ``ModelLibrary``-compatible object."""
        super().__init__(parent)
        if library is None:
            from src.tools.model_explorer.model_library import ModelLibrary

            library = ModelLibrary()
        self.library = library
        self.library_model = LibraryPanelModel.from_library(library)
        self._setup_ui()
        self._populate_library_tree()

    def select_library_entry(self, category: str, key: str) -> bool:
        """Select a library row by category/key for tests and controller callers."""
        if not category:
            raise ValueError("category must be provided")
        if not key:
            raise ValueError("key must be provided")
        for index in range(self.library_tree.topLevelItemCount()):
            group = self.library_tree.topLevelItem(index)
            if group is None:
                continue
            for child_index in range(group.childCount()):
                child = group.child(child_index)
                if child is None:
                    continue
                item_category = child.data(0, Qt.ItemDataRole.UserRole)
                item_key = child.data(0, Qt.ItemDataRole.UserRole + 1)
                if item_category == category and item_key == key:
                    self.library_tree.setCurrentItem(child)
                    return True
        self.status_label.setText(f"Library entry not found: {category}/{key}")
        return False

    def load_selected_as_source(self) -> bool:
        """Load the current library row into the source side of the editor."""
        entry = self.current_entry()
        if entry is None:
            self.status_label.setText("No library model selected")
            return False
        model = self._model_from_entry(entry)
        if model is None:
            return False
        self.editor.left_panel.model = model
        self.editor.left_panel.file_label.setText(f"Library: {entry.name}")
        self.editor.left_panel.save_btn.setEnabled(True)
        self.editor.left_panel._refresh_tree()
        self.status_label.setText(f"Loaded source model: {entry.name}")
        return True

    def load_selected_as_working(self) -> bool:
        """Load the current library row into the editable working side."""
        entry = self.current_entry()
        if entry is None:
            self.status_label.setText("No library model selected")
            return False
        model = self._model_from_entry(entry)
        if model is None:
            return False
        self.editor.right_panel.model = model
        self.editor.right_panel.file_label.setText(f"Library: {entry.name}")
        self.editor.right_panel.save_btn.setEnabled(True)
        self.editor.right_panel._refresh_tree()
        self._refresh_validation_status()
        self.status_label.setText(f"Loaded working model: {entry.name}")
        return True

    def attach_source_to_working(self) -> bool:
        """Attach the loaded source model to the loaded working model."""
        attached = self.editor.attach_source_model_to_working()
        self._refresh_validation_status()
        self.status_label.setText(self.editor.status_label.text())
        return attached

    def export_working_model(self, export_format: ExportFormat = "urdf") -> str | None:
        """Export the composed working model in URDF or MJCF format."""
        content = self.editor.export_working_model(export_format)
        self._refresh_validation_status()
        self.status_label.setText(self.editor.status_label.text())
        return content

    def current_entry(self) -> LibraryModelEntry | None:
        """Return the currently selected library row."""
        item = self.library_tree.currentItem()
        if item is None:
            return None
        category = item.data(0, Qt.ItemDataRole.UserRole)
        key = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not category or not key:
            return None
        for entry in self.library_model.entries:
            if entry.category == category and entry.key == key:
                return entry
        return None

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        library_panel = QWidget()
        library_layout = QVBoxLayout(library_panel)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search models")
        self.search_box.textChanged.connect(self._populate_library_tree)
        library_layout.addWidget(self.search_box)

        self.library_tree = _LibraryEntryTree()
        self.library_tree.setHeaderLabels(["Model", "Format", "Source"])
        self.library_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.library_tree.setDragEnabled(True)
        header = self.library_tree.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        library_layout.addWidget(self.library_tree)

        button_row = QHBoxLayout()
        self.load_source_btn = _DropButton("Source", self._load_entry_as_source)
        self.load_source_btn.clicked.connect(self.load_selected_as_source)
        self.load_working_btn = _DropButton("Working", self._load_entry_as_working)
        self.load_working_btn.clicked.connect(self.load_selected_as_working)
        button_row.addWidget(self.load_source_btn)
        button_row.addWidget(self.load_working_btn)
        library_layout.addLayout(button_row)

        self.editor = FrankensteinEditor()
        splitter.addWidget(library_panel)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        action_row = QHBoxLayout()
        self.attach_btn = QPushButton("Attach")
        self.attach_btn.clicked.connect(self.attach_source_to_working)
        self.export_urdf_btn = QPushButton("URDF")
        self.export_urdf_btn.clicked.connect(lambda: self.export_working_model("urdf"))
        self.export_mjcf_btn = QPushButton("MJCF")
        self.export_mjcf_btn.clicked.connect(lambda: self.export_working_model("mjcf"))
        action_row.addWidget(self.attach_btn)
        action_row.addWidget(self.export_urdf_btn)
        action_row.addWidget(self.export_mjcf_btn)
        layout.addLayout(action_row)

        self.validation_status_label = QLabel("No working model")
        self.status_label = QLabel("Ready")
        layout.addWidget(self.validation_status_label)
        layout.addWidget(self.status_label)

    def _populate_library_tree(self, query: str = "") -> None:
        if query is None:
            raise ValueError("query must be provided")
        self.library_tree.clear()
        for group in self.library_model.grouped_entries(query):
            group_item = QTreeWidgetItem(
                [f"{group.label} ({len(group.entries)})", "", ""]
            )
            group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.library_tree.addTopLevelItem(group_item)
            for entry in group.entries:
                item = QTreeWidgetItem(
                    [entry.name, entry.format_badge, entry.source_label]
                )
                item.setData(0, Qt.ItemDataRole.UserRole, entry.category)
                item.setData(0, Qt.ItemDataRole.UserRole + 1, entry.key)
                if entry.description:
                    item.setToolTip(0, entry.description)
                group_item.addChild(item)
            group_item.setExpanded(True)

    def _model_from_entry(self, entry: LibraryModelEntry) -> URDFModel | None:
        try:
            path = self._path_from_entry(entry)
            model = _load_model_path(path)
        except (OSError, RuntimeError, ValueError) as exc:
            self.status_label.setText(f"Failed to load {entry.name}: {exc}")
            return None
        attachment_points = entry.info.get("attachment_points")
        if isinstance(attachment_points, list):
            model.attachment_points = tuple(
                point for point in attachment_points if isinstance(point, dict)
            )
        return model

    def _load_entry_as_source(self, category: str, key: str) -> bool:
        if not self.select_library_entry(category, key):
            return False
        return self.load_selected_as_source()

    def _load_entry_as_working(self, category: str, key: str) -> bool:
        if not self.select_library_entry(category, key):
            return False
        return self.load_selected_as_working()

    def _path_from_entry(self, entry: LibraryModelEntry) -> Path:
        raw_path = entry.info.get("path") or entry.info.get("urdf_subpath")
        if not raw_path:
            raise ValueError(
                f"Library model '{entry.name}' does not expose a file path"
            )
        path = Path(str(raw_path))
        if path.is_absolute():
            return path
        from src.tools.model_explorer.model_library import _project_root

        return _project_root / path

    def _refresh_validation_status(self) -> None:
        model = self.editor.get_working_model()
        if model is None:
            self.validation_status_label.setText("No working model")
            return
        result = model.validate_composition()
        if result.errors:
            self.validation_status_label.setText(
                f"{len(result.errors)} validation error(s)"
            )
            return
        if result.warnings:
            self.validation_status_label.setText(
                f"{len(result.warnings)} validation warning(s)"
            )
            return
        self.validation_status_label.setText("Validation passed")


def _load_model_path(path: Path) -> URDFModel:
    if path is None:
        raise ValueError("path must be provided")
    suffix = path.suffix.lower()
    if suffix == ".osim":
        from src.tools.model_explorer.osim_loader import OsimLoader

        return _model_from_urdf_xml(OsimLoader().to_urdf(path), path)
    if suffix == ".sdf":
        from src.tools.model_explorer.sdf_loader import SdfLoader

        return _model_from_urdf_xml(SdfLoader().load(path).to_urdf(), path)
    if suffix in {".xml", ".mjcf"} and _is_mujoco_xml(path):
        from model_generation.converters.mjcf_converter import MJCFConverter

        return _model_from_urdf_xml(MJCFConverter().mjcf_to_urdf(path), path)
    return URDFModel.from_file(path)


def _model_from_urdf_xml(xml: str, path: Path) -> URDFModel:
    if not xml.strip():
        raise ValueError("converted URDF XML must be non-empty")
    model = URDFModel.from_element(ET.fromstring(xml), path)
    model.attachment_points = load_attachment_manifest(path).points_as_dicts()
    return model


def _is_mujoco_xml(path: Path) -> bool:
    with path.open(encoding="utf-8", errors="ignore") as handle:
        prefix = handle.read(512)
    return "<mujoco" in prefix


class _LibraryEntryTree(QTreeWidget):
    """Tree that drags stable model-entry identifiers instead of file paths."""

    def mimeData(self, items: list[QTreeWidgetItem]) -> QMimeData:
        data = super().mimeData(items)
        if not items:
            return data
        item = items[0]
        category = item.data(0, Qt.ItemDataRole.UserRole)
        key = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if category and key:
            payload = json.dumps({"category": str(category), "key": str(key)})
            data.setData(_ENTRY_MIME_TYPE, payload.encode("utf-8"))
        return data


class _DropButton(QPushButton):
    """Button target that loads a dragged library entry."""

    def __init__(
        self,
        text: str,
        loader: Callable[[str, str], bool],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        if loader is None:
            raise ValueError("loader must be provided")
        self._loader = loader
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        if event is None:
            return
        mime = event.mimeData()
        if mime is not None and mime.hasFormat(_ENTRY_MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent | None) -> None:
        if event is None:
            return
        payload = _entry_payload(event.mimeData())
        if payload is None:
            return
        category, key = payload
        if self._loader(category, key):
            event.acceptProposedAction()


def _entry_payload(mime: QMimeData | None) -> tuple[str, str] | None:
    if mime is None or not mime.hasFormat(_ENTRY_MIME_TYPE):
        return None
    try:
        payload = json.loads(bytes(mime.data(_ENTRY_MIME_TYPE)).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    category = str(payload.get("category", "")).strip()
    key = str(payload.get("key", "")).strip()
    if not category or not key:
        return None
    return category, key
