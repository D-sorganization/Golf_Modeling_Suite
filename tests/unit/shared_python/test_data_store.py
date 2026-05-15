"""Unit tests for src/shared/data_store/store.py.

Covers:
- Issue #5453: flush_to_disk raises NotImplementedError when storage_path is set
- Issue #5454: SwingDataSequence.__post_init__ validates all per-timestep arrays
"""

import numpy as np
import pytest

from src.shared.data_store.store import SimulationDataStore, SwingDataSequence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sequence(
    n: int = 4,
    n_joints: int = 3,
    sequence_id: str = "seq-1",
    joint_velocities_len: int | None = None,
    club_pose_len: int | None = None,
    applied_torques_len: int | None = None,
) -> SwingDataSequence:
    """Return a valid SwingDataSequence, with optional length overrides for testing."""
    jv_len = n if joint_velocities_len is None else joint_velocities_len
    cp_len = n if club_pose_len is None else club_pose_len
    at_len = n if applied_torques_len is None else applied_torques_len
    return SwingDataSequence(
        sequence_id=sequence_id,
        timestamps=np.linspace(0.0, 1.0, n),
        joint_angles=np.zeros((n, n_joints)),
        joint_velocities=np.zeros((jv_len, n_joints)),
        club_pose=np.zeros((cp_len, 7)),
        applied_torques=np.zeros((at_len, n_joints)),
    )


# ---------------------------------------------------------------------------
# Issue #5453 — flush_to_disk
# ---------------------------------------------------------------------------


class TestFlushToDisk:
    def test_flush_no_storage_path_returns_silently(self):
        store = SimulationDataStore(storage_path=None)
        store.add_sequence(_make_sequence())
        # Must not raise
        store.flush_to_disk()

    def test_flush_with_storage_path_raises_not_implemented(self, tmp_path):
        store = SimulationDataStore(storage_path=str(tmp_path / "data.h5"))
        store.add_sequence(_make_sequence())
        with pytest.raises(NotImplementedError) as exc_info:
            store.flush_to_disk()
        assert "flush_to_disk" in str(exc_info.value)
        assert "not yet implemented" in str(exc_info.value)
        assert "not persisted" in str(exc_info.value)

    def test_flush_with_storage_path_raises_even_when_store_is_empty(self, tmp_path):
        store = SimulationDataStore(storage_path=str(tmp_path / "empty.h5"))
        with pytest.raises(NotImplementedError):
            store.flush_to_disk()


# ---------------------------------------------------------------------------
# Issue #5454 — SwingDataSequence per-timestep length validation
# ---------------------------------------------------------------------------


class TestSwingDataSequenceValidation:
    def test_valid_sequence_initialises_without_error(self):
        seq = _make_sequence(n=5)
        assert seq.sequence_id == "seq-1"

    # joint_angles (existing check — regression guard)
    def test_joint_angles_wrong_length_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            SwingDataSequence(
                sequence_id="bad",
                timestamps=np.linspace(0, 1, 4),
                joint_angles=np.zeros((3, 2)),  # wrong: 3 != 4
                joint_velocities=np.zeros((4, 2)),
                club_pose=np.zeros((4, 7)),
                applied_torques=np.zeros((4, 2)),
            )
        assert "joint_angles" in str(exc_info.value)

    # joint_velocities
    def test_joint_velocities_wrong_length_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            _make_sequence(n=4, joint_velocities_len=3)
        assert "joint_velocities" in str(exc_info.value)
        assert "3" in str(exc_info.value)
        assert "4" in str(exc_info.value)

    def test_joint_velocities_error_message_contains_field_name(self):
        with pytest.raises(
            ValueError, match=r"joint_velocities length \d+ != timestamps length \d+"
        ):
            _make_sequence(n=5, joint_velocities_len=2)

    # club_pose
    def test_club_pose_wrong_length_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            _make_sequence(n=4, club_pose_len=5)
        assert "club_pose" in str(exc_info.value)
        assert "5" in str(exc_info.value)
        assert "4" in str(exc_info.value)

    def test_club_pose_error_message_contains_field_name(self):
        with pytest.raises(
            ValueError, match=r"club_pose length \d+ != timestamps length \d+"
        ):
            _make_sequence(n=6, club_pose_len=3)

    # applied_torques
    def test_applied_torques_wrong_length_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            _make_sequence(n=4, applied_torques_len=2)
        assert "applied_torques" in str(exc_info.value)
        assert "2" in str(exc_info.value)
        assert "4" in str(exc_info.value)

    def test_applied_torques_error_message_contains_field_name(self):
        with pytest.raises(
            ValueError, match=r"applied_torques length \d+ != timestamps length \d+"
        ):
            _make_sequence(n=3, applied_torques_len=7)

    # joint_velocities mismatch takes priority over later checks
    def test_first_failing_field_error_is_reported(self):
        """joint_velocities is checked before club_pose; its error is raised first."""
        with pytest.raises(ValueError) as exc_info:
            SwingDataSequence(
                sequence_id="multi-bad",
                timestamps=np.linspace(0, 1, 4),
                joint_angles=np.zeros((4, 2)),
                joint_velocities=np.zeros((3, 2)),  # wrong
                club_pose=np.zeros((2, 7)),  # also wrong
                applied_torques=np.zeros((1, 2)),  # also wrong
            )
        assert "joint_velocities" in str(exc_info.value)
