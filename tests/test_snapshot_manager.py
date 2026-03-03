"""Tests for SnapshotManager: save, load, list, delete, clear."""

import pytest
from src.core.level import Level
from src.core.snapshot_manager import SnapshotManager


LEVEL_DATA = (
    "#####\n"
    "#@$.#\n"
    "#   #\n"
    "#####"
)


@pytest.fixture
def level():
    return Level(level_data=LEVEL_DATA)


@pytest.fixture
def manager():
    return SnapshotManager()


class TestSaveLoad:

    def test_save_returns_name(self, manager, level):
        name = manager.save_snapshot(level)
        assert isinstance(name, str)
        assert len(name) > 0

    def test_save_custom_name(self, manager, level):
        name = manager.save_snapshot(level, name="before_push")
        assert name == "before_push"

    def test_load_restores_state(self, manager, level):
        manager.save_snapshot(level, "s1")
        level.move(1, 0)
        assert level.moves == 1
        assert manager.load_snapshot(level, "s1")
        assert level.moves == 0
        assert level.player_pos == (1, 1)

    def test_load_restores_boxes(self, manager, level):
        original_boxes = list(level.boxes)
        manager.save_snapshot(level, "s1")
        level.move(1, 0)  # push
        assert level.boxes != original_boxes
        manager.load_snapshot(level, "s1")
        assert level.boxes == original_boxes

    def test_load_clears_redo_stack(self, manager, level):
        level.move(1, 0)
        level.undo()
        assert len(level.redo_stack) == 1
        manager.save_snapshot(level, "s1")
        manager.load_snapshot(level, "s1")
        assert level.redo_stack == []

    def test_load_nonexistent(self, manager, level):
        assert not manager.load_snapshot(level, "nope")

    def test_load_latest(self, manager, level):
        manager.save_snapshot(level, "s1")
        level.move(1, 0)
        manager.save_snapshot(level, "s2")

        # Reset to initial
        level.undo()
        assert manager.load_latest(level)
        assert level.moves == 1  # s2 had moves=1

    def test_load_latest_empty(self, manager, level):
        assert not manager.load_latest(level)


class TestListDelete:

    def test_list_empty(self, manager):
        assert manager.list_snapshots() == []

    def test_list_sorted_newest_first(self, manager, level):
        manager.save_snapshot(level, "s1")
        level.move(1, 0)
        manager.save_snapshot(level, "s2")
        snaps = manager.list_snapshots()
        assert len(snaps) == 2
        assert snaps[0].name == "s2"

    def test_delete(self, manager, level):
        manager.save_snapshot(level, "s1")
        assert manager.delete_snapshot("s1")
        assert manager.list_snapshots() == []

    def test_delete_nonexistent(self, manager):
        assert not manager.delete_snapshot("nope")

    def test_clear(self, manager, level):
        manager.save_snapshot(level, "s1")
        manager.save_snapshot(level, "s2")
        manager.clear()
        assert manager.list_snapshots() == []


class TestHistoryPreservation:

    def test_snapshot_preserves_history(self, manager, level):
        level.move(1, 0)
        level.move(0, 1)
        manager.save_snapshot(level, "s1")

        # Undo everything
        level.undo()
        level.undo()
        assert len(level.history) == 0

        # Load snapshot should restore history
        manager.load_snapshot(level, "s1")
        assert len(level.history) == 2

    def test_snapshot_history_is_independent(self, manager, level):
        """Modifying level history after save should not affect snapshot."""
        level.move(1, 0)
        manager.save_snapshot(level, "s1")
        level.move(0, 1)
        level.move(0, 1)

        manager.load_snapshot(level, "s1")
        assert len(level.history) == 1
