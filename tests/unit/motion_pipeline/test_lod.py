"""Law-of-Demeter import-graph test for the motion pipeline contracts.

The motion pipeline CIR sits at the bottom of the dependency tree; it
must not import from engines, api, learning, apps, tools, or
deployment. This test parses ``contracts.py`` via ``ast`` and asserts
the rule.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CONTRACTS_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "shared"
    / "python"
    / "motion_pipeline"
    / "contracts.py"
)

FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "src.engines",
    "src.api",
    "src.learning",
    "src.apps",
    "src.tools",
    "src.deployment",
    "engines.",
    "api.",
    "learning.",
    "apps.",
    "tools.",
    "deployment.",
)


def _collect_imported_modules(source: str) -> list[str]:
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def test_contracts_file_exists() -> None:
    assert CONTRACTS_PATH.is_file(), f"{CONTRACTS_PATH} not found"


def test_contracts_imports_respect_lod() -> None:
    source = CONTRACTS_PATH.read_text(encoding="utf-8")
    modules = _collect_imported_modules(source)
    violations = [
        m for m in modules if any(m.startswith(p) for p in FORBIDDEN_PREFIXES)
    ]
    assert not violations, (
        f"contracts.py must not import from forbidden layers; found: {violations}"
    )


@pytest.mark.parametrize("forbidden", FORBIDDEN_PREFIXES)
def test_no_specific_forbidden_prefix_imported(forbidden: str) -> None:
    source = CONTRACTS_PATH.read_text(encoding="utf-8")
    modules = _collect_imported_modules(source)
    bad = [m for m in modules if m.startswith(forbidden)]
    assert not bad, f"forbidden import prefix '{forbidden}' present: {bad}"
