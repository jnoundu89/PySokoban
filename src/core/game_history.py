"""
Game History Manager with Choice Points for Sokoban Game.

Tracks decision points where the player had multiple significant options
(e.g., could push different boxes, multiple directions available).
Provides navigation between choice points for efficient undo/redo.
"""

from src.core.constants import WALL


class GameHistoryManager:
    """
    Manages choice point detection and navigation within the level's history.

    A "choice point" is a state where the player has multiple meaningful
    options: they can push in several directions, reach multiple boxes, etc.
    """

    def __init__(self):
        self.choice_points = []  # Indices into the level.history stack

    def record_move(self, level, was_push):
        """
        Record a move and check if the state before it was a choice point.

        Should be called AFTER level.move() succeeds.

        Args:
            level: The Level object.
            was_push: Whether the last move was a box push.
        """
        history_index = len(level.history) - 1
        if history_index < 0:
            return

        # Check the state we just left (now in history)
        state = level.history[history_index]
        if self._is_choice_point(level, state, was_push):
            if not self.choice_points or self.choice_points[-1] != history_index:
                self.choice_points.append(history_index)

    def _is_choice_point(self, level, state, was_push):
        """
        Determine if a given state represents a meaningful choice point.

        A state is a choice point if:
        - The player could push a box (was_push=True) AND could also push
          in at least one other direction, OR
        - The player has 3+ free directions to move (intersection), OR
        - The player is adjacent to 2+ pushable boxes
        """
        player_pos = state['player_pos']
        boxes = state['boxes']
        px, py = player_pos

        # Count available push directions
        push_directions = 0
        # Count adjacent pushable boxes
        pushable_boxes = 0
        # Count free move directions
        free_directions = 0

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = px + dx, py + dy

            # Check if we can move there
            if (0 <= nx < level.width and 0 <= ny < level.height and
                    not level.is_wall(nx, ny)):

                if (nx, ny) in boxes:
                    # There's a box — can we push it?
                    bx, by = nx + dx, ny + dy
                    if (0 <= bx < level.width and 0 <= by < level.height and
                            not level.is_wall(bx, by) and (bx, by) not in boxes):
                        push_directions += 1
                        pushable_boxes += 1
                else:
                    free_directions += 1

        # Choice point criteria
        if was_push and push_directions >= 2:
            return True
        if pushable_boxes >= 2:
            return True
        if free_directions >= 3:
            return True

        return False

    def get_previous_choice_point(self, level):
        """
        Get the history index of the previous choice point.

        Args:
            level: The Level object.

        Returns:
            int or None: History index of the previous choice point.
        """
        current_len = len(level.history)
        for i in range(len(self.choice_points) - 1, -1, -1):
            if self.choice_points[i] < current_len - 1:
                return self.choice_points[i]
        return None

    def get_next_choice_point(self, level):
        """
        Get the redo-stack index of the next choice point.
        This is conceptual — we look at redo_stack indices.

        Returns:
            int or None: Not directly applicable for redo navigation,
                         returns the count of redos needed, or None.
        """
        # The redo stack doesn't track choice points in the same way,
        # so we return None and let the caller redo step-by-step.
        return None

    def jump_to_choice_point(self, level, target_index):
        """
        Jump to a specific choice point by undoing moves.

        Args:
            level: The Level object.
            target_index: History index to jump to.

        Returns:
            int: Number of undos performed.
        """
        undos = 0
        while len(level.history) > target_index + 1:
            if not level.undo():
                break
            undos += 1
        return undos

    def undo_to_previous_choice_point(self, level):
        """
        Undo moves back to the previous choice point.

        Args:
            level: The Level object.

        Returns:
            int: Number of undos performed, 0 if no choice point found.
        """
        target = self.get_previous_choice_point(level)
        if target is None:
            # No choice point found — undo everything to start
            if level.history:
                return self.jump_to_choice_point(level, -1)
            return 0
        return self.jump_to_choice_point(level, target)

    def clear(self):
        """Clear all recorded choice points."""
        self.choice_points.clear()
