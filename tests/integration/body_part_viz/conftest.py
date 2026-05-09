"""Shared pytest configuration for body_part_viz integration tests.

Adds a ``--update-goldens`` flag the renderer-snapshots test uses to
write expected hashes back to ``tests/fixtures/body_part_viz/`` instead
of comparing against them.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Rewrite golden hashes for body_part_viz snapshot tests.",
    )


@pytest.fixture
def update_goldens(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-goldens"))
