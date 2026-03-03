"""
Snapshot Manager for Sokoban Game.

Provides named save/load of complete game states, allowing players to
explore multiple solution branches and return to any saved point.
"""

import copy
import time


class Snapshot:
    """A named snapshot of the complete game state."""

    __slots__ = ('name', 'timestamp', 'player_pos', 'boxes', 'moves',
                 'pushes', 'history')

    def __init__(self, name, player_pos, boxes, moves, pushes, history):
        self.name = name
        self.timestamp = time.time()
        self.player_pos = player_pos
        self.boxes = boxes
        self.moves = moves
        self.pushes = pushes
        self.history = history


class SnapshotManager:
    """Manages named snapshots of game state."""

    def __init__(self):
        self.snapshots = {}
        self._auto_counter = 0

    def save_snapshot(self, level, name=None):
        """
        Save current level state as a named snapshot.

        Args:
            level: The Level object to snapshot.
            name: Optional name. Auto-generated if None.

        Returns:
            str: The name of the saved snapshot.
        """
        if name is None:
            self._auto_counter += 1
            name = f"Quick Save #{self._auto_counter}"

        snapshot = Snapshot(
            name=name,
            player_pos=level.player_pos,
            boxes=list(level.boxes),
            moves=level.moves,
            pushes=level.pushes,
            history=copy.deepcopy(level.history)
        )
        self.snapshots[name] = snapshot
        return name

    def load_snapshot(self, level, name):
        """
        Load a named snapshot into the level.

        Args:
            level: The Level object to restore into.
            name: Name of the snapshot to load.

        Returns:
            bool: True if loaded successfully.
        """
        snapshot = self.snapshots.get(name)
        if snapshot is None:
            return False

        level.player_pos = snapshot.player_pos
        level.boxes = list(snapshot.boxes)
        level.moves = snapshot.moves
        level.pushes = snapshot.pushes
        level.history = copy.deepcopy(snapshot.history)
        level.redo_stack = []
        return True

    def load_latest(self, level):
        """
        Load the most recent snapshot.

        Args:
            level: The Level object to restore into.

        Returns:
            bool: True if loaded successfully.
        """
        if not self.snapshots:
            return False

        latest = max(self.snapshots.values(), key=lambda s: s.timestamp)
        return self.load_snapshot(level, latest.name)

    def list_snapshots(self):
        """
        List all snapshots sorted by timestamp (newest first).

        Returns:
            list[Snapshot]: List of snapshots.
        """
        return sorted(self.snapshots.values(),
                      key=lambda s: s.timestamp, reverse=True)

    def delete_snapshot(self, name):
        """
        Delete a named snapshot.

        Args:
            name: Name of the snapshot to delete.

        Returns:
            bool: True if deleted successfully.
        """
        if name in self.snapshots:
            del self.snapshots[name]
            return True
        return False

    def clear(self):
        """Clear all snapshots."""
        self.snapshots.clear()
        self._auto_counter = 0
