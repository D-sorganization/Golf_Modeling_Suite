from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_STANDARD = REPO_ROOT / ".github" / "workflows" / "ci-standard.yml"
TAURI_BUILD = REPO_ROOT / ".github" / "workflows" / "tauri-build.yml"
DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [REPO_ROOT / line for line in result.stdout.splitlines()]


def test_ui_has_single_tracked_package_manifest() -> None:
    package_files = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REPO_ROOT.glob("*/*")
        if path.name == "package.json" and "node_modules" not in path.parts
    ]
    root_package = REPO_ROOT / "package.json"
    if root_package.exists():
        package_files.append(root_package.relative_to(REPO_ROOT).as_posix())

    assert sorted(package_files) == ["ui/package.json"]


def test_legacy_create_react_app_surface_is_removed() -> None:
    tracked_text_files = [
        path
        for path in _tracked_files()
        if path.is_file()
        and "node_modules" not in path.parts
        and path.suffix.lower()
        in {".json", ".md", ".yml", ".yaml", ".toml", ".ts", ".tsx", ".js"}
    ]

    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in tracked_text_files
        if "react-scripts" in path.read_text(encoding="utf-8", errors="ignore")
    ]

    assert offenders == []


def test_ci_runs_blocking_ui_security_and_quality_checks() -> None:
    workflow = CI_STANDARD.read_text(encoding="utf-8")

    for command in (
        "npm audit --audit-level=high",
        "npm run lint",
        "npm run type-check",
        "npm run test:run",
        "npm run build",
    ):
        assert command in workflow

    frontend_job = workflow.split("frontend-tests:", maxsplit=1)[1]
    frontend_job = frontend_job.split("matlab-tests:", maxsplit=1)[0]
    assert "continue-on-error" not in frontend_job


def test_tauri_build_workflow_uses_current_product_name() -> None:
    workflow = TAURI_BUILD.read_text(encoding="utf-8")

    assert "Builds UpstreamDrift as a native desktop app using Tauri 2" in workflow
    assert "Golf Modeling Suite" not in workflow


def test_dependabot_tracks_vite_tauri_ui_manifest() -> None:
    config = DEPENDABOT.read_text(encoding="utf-8")

    assert 'package-ecosystem: "npm"' in config
    assert 'directory: "/ui"' in config
    assert 'directory: "/src/ui"' not in config


def test_contributing_documents_the_ui_build_surface() -> None:
    docs = CONTRIBUTING.read_text(encoding="utf-8")
    package_json = json.loads((REPO_ROOT / "ui" / "package.json").read_text())

    assert "## Building the UI" in docs
    assert "cd ui && npm install && npm run dev" in docs
    assert "cd ui && npm run build" in docs
    assert package_json["scripts"]["build"] == "tsc -b && vite build"
