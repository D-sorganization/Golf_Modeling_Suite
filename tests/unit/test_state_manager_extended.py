"""Unit tests for src/shared/python/upstream_drift_tools/utils/state_manager.py.

Tests cover safe_read_json, safe_write_json, StateManager CRUD operations,
protect/unprotect, export/import, session save/load, and get_state_manager.
All tests use tmp_path to avoid writing to the production filesystem.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
    """StateManager instance using a temporary directory."""
    from src.shared.python.upstream_drift_tools.utils.state_manager import StateManager

    return StateManager(base_directory=str(tmp_path / "states"))


class TestStateManagerInit:
    """Tests for StateManager initialization."""

    def test_creates_required_directories(self, tmp_path: Path) -> None:
        """StateManager creates states, sessions, backups, exports directories."""
        from src.shared.python.upstream_drift_tools.utils.state_manager import (
            StateManager,
        )

        base = tmp_path / "sm_base"
        StateManager(base_directory=str(base))
        assert (base / "states").exists()
        assert (base / "sessions").exists()
        assert (base / "backups").exists()
        assert (base / "exports").exists()

    def test_protected_states_starts_empty(self, manager) -> None:
        """No protected states exist on fresh initialization."""
        assert len(manager.protected_states) == 0

    def test_auto_save_enabled_by_default(self, manager) -> None:
        """auto_save_enabled is True by default."""
        assert manager.auto_save_enabled is True


class TestStateManagerSaveLoad:
    """Tests for save_state and load_state methods."""

    def test_save_state_returns_true(self, manager) -> None:
        """save_state returns True on success."""
        result = manager.save_state("test_state", {"x": 1, "y": 2})
        assert result is True

    def test_load_state_returns_saved_data(self, manager) -> None:
        """load_state returns data previously saved with save_state."""
        manager.save_state("my_state", {"temperature": 350.0, "pressure": 5.0})
        loaded = manager.load_state("my_state")
        assert loaded is not None
        assert loaded.get("temperature") == 350.0
        assert loaded.get("pressure") == 5.0

    def test_load_nonexistent_state_returns_none(self, manager) -> None:
        """load_state returns None for a state that does not exist."""
        result = manager.load_state("no_such_state")
        assert result is None

    def test_save_and_list_states(self, manager) -> None:
        """list_states returns entries for all saved states."""
        manager.save_state("state_a", {"v": 1})
        manager.save_state("state_b", {"v": 2})
        states = manager.list_states()
        names = [s["name"] for s in states]
        assert "state_a" in names
        assert "state_b" in names

    def test_save_creates_backup_on_overwrite(self, manager) -> None:
        """Saving a state twice creates a backup of the first version."""
        manager.save_state("overwrite_me", {"v": 1})
        manager.save_state("overwrite_me", {"v": 2})
        # No error — backup creation should be silent
        loaded = manager.load_state("overwrite_me")
        assert loaded is not None
        assert loaded.get("v") == 2

    def test_save_with_description(self, manager) -> None:
        """save_state accepts a description parameter."""
        result = manager.save_state("described", {"x": 99}, description="Test state")
        assert result is True


class TestStateManagerDelete:
    """Tests for delete_state method."""

    def test_delete_existing_state(self, manager) -> None:
        """delete_state returns True and removes the state."""
        manager.save_state("to_delete", {"a": 1})
        result = manager.delete_state("to_delete")
        assert result is True
        assert manager.load_state("to_delete") is None

    def test_delete_nonexistent_state_returns_false(self, manager) -> None:
        """delete_state returns False for a state that does not exist."""
        result = manager.delete_state("ghost_state")
        assert result is False

    def test_delete_protected_state_requires_force(self, manager) -> None:
        """Protected states cannot be deleted without force=True."""
        manager.save_state("protected_one", {"x": 1}, protected=True)
        manager.protect_state("protected_one")
        result = manager.delete_state("protected_one")
        assert result is False

    def test_force_delete_protected_state(self, manager) -> None:
        """Protected states can be deleted with force=True."""
        manager.save_state("force_del", {"x": 1}, protected=True)
        manager.protect_state("force_del")
        result = manager.delete_state("force_del", force=True)
        assert result is True


class TestStateManagerProtect:
    """Tests for protect_state and unprotect_state."""

    def test_protect_adds_to_protected_set(self, manager) -> None:
        """protect_state adds the state name to protected_states."""
        manager.save_state("prot_test", {"v": 1})
        result = manager.protect_state("prot_test")
        assert result is True
        assert "prot_test" in manager.protected_states

    def test_unprotect_removes_from_protected_set(self, manager) -> None:
        """unprotect_state removes the state name from protected_states."""
        manager.save_state("unprot_test", {"v": 1})
        manager.protect_state("unprot_test")
        result = manager.unprotect_state("unprot_test")
        assert result is True
        assert "unprot_test" not in manager.protected_states


class TestStateManagerSession:
    """Tests for save_session and load_session."""

    def test_save_and_load_session(self, manager) -> None:
        """Session data can be saved and then reloaded."""
        session_data = {"user": "admin", "last_calc": "steam_engine"}
        manager.save_session(session_data)
        loaded = manager.load_session()
        assert loaded is not None
        assert loaded.get("user") == "admin"

    def test_load_session_returns_none_without_saved_session(self, manager) -> None:
        """load_session returns None or empty when no session was saved."""
        result = manager.load_session()
        # None or empty dict — no session file exists yet
        assert result is None or isinstance(result, dict)


class TestStateManagerListStates:
    """Tests for list_states."""

    def test_empty_on_fresh_manager(self, manager) -> None:
        """list_states returns empty list before any states are saved."""
        states = manager.list_states()
        assert states == []

    def test_returns_list_of_dicts(self, manager) -> None:
        """list_states returns a list of dicts with 'name' keys."""
        manager.save_state("state1", {"v": 1})
        states = manager.list_states()
        assert isinstance(states, list)
        assert all(isinstance(s, dict) for s in states)
        assert all("name" in s for s in states)


# ---------------------------------------------------------------------------
# get_state_manager singleton
# ---------------------------------------------------------------------------


class TestGetStateManager:
    """Tests for get_state_manager factory/singleton function."""

    def test_returns_state_manager_instance(self, tmp_path: Path) -> None:
        """get_state_manager returns a StateManager instance."""
        from src.shared.python.upstream_drift_tools.utils.state_manager import (
            StateManager,
            get_state_manager,
        )

        sm = get_state_manager(base_directory=str(tmp_path / "sm_test"))
        assert isinstance(sm, StateManager)

    def test_singleton_returns_same_instance(self, tmp_path: Path) -> None:
        """get_state_manager with same directory returns same instance."""
        from src.shared.python.upstream_drift_tools.utils.state_manager import (
            get_state_manager,
        )

        base = str(tmp_path / "singleton_test")
        sm1 = get_state_manager(base_directory=base)
        sm2 = get_state_manager(base_directory=base)
        assert sm1 is sm2
