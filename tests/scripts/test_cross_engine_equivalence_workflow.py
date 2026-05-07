from __future__ import annotations

from pathlib import Path


def test_equivalence_workflow_recovers_recordless_pip_install() -> None:
    workflow = Path(".github/workflows/cross-engine-equivalence.yml").read_text(
        encoding="utf-8"
    )

    assert "python -m pip install --upgrade pip || \\" in workflow
    assert (
        "python -m pip install --ignore-installed --no-deps --upgrade pip" in workflow
    )
