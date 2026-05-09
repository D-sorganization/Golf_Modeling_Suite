"""Regression tests for issue #4721: c3d adapter must raise typed errors.

Before the fix, an empty or corrupt ``.c3d`` file leaked the underlying
``ezc3d`` ``OSError`` instead of the canonical
``AdapterContractError``. These tests guard the typed-error contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ezc3d = pytest.importorskip(
    "ezc3d", reason="c3d typed-error contract requires ezc3d at runtime"
)

from src.shared.python.motion_pipeline.sources.base import (  # noqa: E402
    AdapterContractError,
)
from src.shared.python.motion_pipeline.sources.c3d_adapter import (  # noqa: E402
    C3DAdapter,
)


@pytest.fixture
def adapter() -> C3DAdapter:
    return C3DAdapter()


def test_empty_c3d_file_raises_typed_error(tmp_path: Path, adapter: C3DAdapter) -> None:
    p = tmp_path / "empty.c3d"
    p.write_bytes(b"")
    with pytest.raises(AdapterContractError, match="empty"):
        adapter.load(p)


def test_truncated_c3d_file_raises_typed_error(
    tmp_path: Path, adapter: C3DAdapter
) -> None:
    p = tmp_path / "truncated.c3d"
    p.write_bytes(b"\x02\x50" + b"\x00" * 14)  # 16 bytes of pseudo-header
    with pytest.raises(AdapterContractError):
        adapter.load(p)


def test_non_c3d_file_raises_typed_error(tmp_path: Path, adapter: C3DAdapter) -> None:
    p = tmp_path / "nope.c3d"
    p.write_text("this is not a c3d file at all\n" * 4)
    with pytest.raises(AdapterContractError):
        adapter.load(p)


def test_typed_error_message_mentions_path(tmp_path: Path, adapter: C3DAdapter) -> None:
    p = tmp_path / "missing-bytes.c3d"
    p.write_bytes(b"")
    with pytest.raises(AdapterContractError) as excinfo:
        adapter.load(p)
    assert str(p) in str(excinfo.value)
