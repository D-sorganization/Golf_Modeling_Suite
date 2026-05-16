"""Tests for SimulationDataStore — issue #5477.

Covers:
- Construction with and without a storage_path
- Time-series add / retrieval
- Validation rejection of mismatched dimensions
- flush_to_disk must NOT raise NotImplementedError (the regression bug)
- HDF5 round-trip persistence when a path is supplied
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.shared.data_store.store import SimulationDataStore, SwingDataSequence


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_sequence(
    seq_id: str = "test-seq", n: int = 10, j: int = 6
) -> SwingDataSequence:
    """Create a valid SwingDataSequence for testing."""
    return SwingDataSequence(
        sequence_id=seq_id,
        timestamps=np.linspace(0.0, 1.0, n),
        joint_angles=np.zeros((n, j)),
        joint_velocities=np.zeros((n, j)),
        club_pose=np.zeros((n, 7)),
        applied_torques=np.zeros((n, j)),
        metadata={"engine": "mock"},
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_construction_without_path_succeeds() -> None:
    """Store can be created without a storage_path."""
    store = SimulationDataStore()
    assert store is not None


def test_construction_with_path_succeeds(tmp_path: Path) -> None:
    """Store can be created with a storage_path (file need not exist yet)."""
    path = tmp_path / "test_store.h5"
    store = SimulationDataStore(storage_path=str(path))
    assert store is not None


# ---------------------------------------------------------------------------
# Add / retrieve / list
# ---------------------------------------------------------------------------


def test_add_timeseries_stores_values() -> None:
    """Added sequence is retrievable by ID."""
    store = SimulationDataStore()
    seq = _make_sequence("abc-123")
    store.add_sequence(seq)
    retrieved = store.get_sequence("abc-123")
    assert retrieved.sequence_id == "abc-123"
    np.testing.assert_array_equal(retrieved.timestamps, seq.timestamps)


def test_list_sequences_returns_ids() -> None:
    """list_sequences returns all added IDs."""
    store = SimulationDataStore()
    store.add_sequence(_make_sequence("s1"))
    store.add_sequence(_make_sequence("s2"))
    ids = store.list_sequences()
    assert set(ids) == {"s1", "s2"}


def test_add_duplicate_raises_key_error() -> None:
    """Adding a sequence with an existing ID raises KeyError."""
    store = SimulationDataStore()
    store.add_sequence(_make_sequence("dup"))
    with pytest.raises(KeyError, match="dup"):
        store.add_sequence(_make_sequence("dup"))


def test_get_missing_sequence_raises() -> None:
    """Retrieving a non-existent sequence raises KeyError."""
    store = SimulationDataStore()
    with pytest.raises(KeyError):
        store.get_sequence("nonexistent")


# ---------------------------------------------------------------------------
# Validation rejection
# ---------------------------------------------------------------------------


def test_validation_rejects_mismatched_dimensions() -> None:
    """SwingDataSequence.__post_init__ rejects mismatched timestamps vs angles."""
    with pytest.raises(ValueError, match="Mismatched"):
        SwingDataSequence(
            sequence_id="bad",
            timestamps=np.linspace(0, 1, 10),
            joint_angles=np.zeros((5, 6)),  # wrong N
            joint_velocities=np.zeros((10, 6)),
            club_pose=np.zeros((10, 7)),
            applied_torques=np.zeros((10, 6)),
        )


def test_validation_rejects_mismatched_velocities() -> None:
    """SwingDataSequence rejects mismatched timestamps vs velocities."""
    with pytest.raises(ValueError, match="[Mm]ismatched"):
        SwingDataSequence(
            sequence_id="bad2",
            timestamps=np.linspace(0, 1, 10),
            joint_angles=np.zeros((10, 6)),
            joint_velocities=np.zeros((7, 6)),  # wrong N
            club_pose=np.zeros((10, 7)),
            applied_torques=np.zeros((10, 6)),
        )


# ---------------------------------------------------------------------------
# flush_to_disk — the regression bug
# ---------------------------------------------------------------------------


def test_flush_to_disk_does_not_raise_without_path() -> None:
    """flush_to_disk with no storage_path is a no-op (does not raise)."""
    store = SimulationDataStore()
    store.add_sequence(_make_sequence())
    # Must not raise any exception, especially not NotImplementedError
    store.flush_to_disk()


def test_flush_to_disk_does_not_raise_not_implemented_with_path(tmp_path: Path) -> None:
    """flush_to_disk with a storage_path must not raise NotImplementedError.

    This is the regression test for issue #5477.
    """
    path = tmp_path / "store.h5"
    store = SimulationDataStore(storage_path=str(path))
    store.add_sequence(_make_sequence("run-001"))
    # The key assertion — must not raise NotImplementedError
    store.flush_to_disk()


# ---------------------------------------------------------------------------
# HDF5 round-trip persistence
# ---------------------------------------------------------------------------


def test_flush_and_reload_round_trip(tmp_path: Path) -> None:
    """Data written to HDF5 can be reloaded into a new store instance."""
    path = tmp_path / "store_rt.h5"
    seq = _make_sequence("rt-001", n=20, j=8)

    # Write
    store_write = SimulationDataStore(storage_path=str(path))
    store_write.add_sequence(seq)
    store_write.flush_to_disk()

    # Read back in a fresh store
    store_read = SimulationDataStore(storage_path=str(path))
    store_read.load_from_disk()

    assert "rt-001" in store_read.list_sequences()
    retrieved = store_read.get_sequence("rt-001")
    np.testing.assert_array_almost_equal(retrieved.timestamps, seq.timestamps)
    np.testing.assert_array_almost_equal(retrieved.joint_angles, seq.joint_angles)


def test_flush_creates_hdf5_file(tmp_path: Path) -> None:
    """flush_to_disk actually creates a file at storage_path."""
    path = tmp_path / "output.h5"
    assert not path.exists()

    store = SimulationDataStore(storage_path=str(path))
    store.add_sequence(_make_sequence("check"))
    store.flush_to_disk()

    assert path.exists(), "HDF5 file was not created by flush_to_disk"


# ---------------------------------------------------------------------------
# DbC — precondition checks
# ---------------------------------------------------------------------------


def test_add_sequence_rejects_none() -> None:
    """add_sequence rejects None input with ValueError/TypeError."""
    store = SimulationDataStore()
    with pytest.raises((ValueError, TypeError)):
        store.add_sequence(None)  # type: ignore[arg-type]


def test_get_sequence_rejects_empty_id() -> None:
    """get_sequence rejects empty string ID."""
    store = SimulationDataStore()
    with pytest.raises((ValueError, KeyError)):
        store.get_sequence("")
