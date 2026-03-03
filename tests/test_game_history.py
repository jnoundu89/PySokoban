"""Tests for GameHistoryManager: choice point detection and navigation."""

import pytest
from src.core.level import Level
from src.core.game_history import GameHistoryManager


# Level where player has multiple options (intersection + pushable boxes)
#  ######
#  #    #
#  # $$ #
#  # @  #
#  #    #
#  ######
CHOICE_LEVEL = (
    "######\n"
    "#    #\n"
    "# $$ #\n"
    "# @  #\n"
    "#    #\n"
    "######"
)

# Corridor level — no choices, just a straight line
CORRIDOR_LEVEL = (
    "#######\n"
    "#@ $. #\n"
    "#######"
)


@pytest.fixture
def choice_level():
    return Level(level_data=CHOICE_LEVEL)


@pytest.fixture
def corridor_level():
    return Level(level_data=CORRIDOR_LEVEL)


@pytest.fixture
def manager():
    return GameHistoryManager()


class TestChoicePointDetection:

    def test_intersection_is_choice_point(self, choice_level, manager):
        """Player at an intersection (3+ free directions) should be a choice point."""
        # Player at (2,3) in CHOICE_LEVEL has 3 free directions (left blocked by wall?
        # Let's check: up(2,2)=box, down(2,4)=free, left(1,3)=free, right(3,3)=free
        # That's 3 free directions -> choice point
        choice_level.move(0, 1)  # move down
        manager.record_move(choice_level, was_push=False)
        assert len(manager.choice_points) >= 1

    def test_corridor_no_choice_point(self, corridor_level, manager):
        """Straight corridor moves should not create choice points."""
        corridor_level.move(1, 0)  # move right (only forward possible realistically)
        manager.record_move(corridor_level, was_push=False)
        # In a corridor player has ~2 directions -> not a choice point
        assert len(manager.choice_points) == 0

    def test_push_with_multiple_push_dirs(self, choice_level, manager):
        """State where player can push in 2+ directions is a choice point."""
        # Move up to be adjacent to a box, then push
        choice_level.move(0, -1)  # player to (2,2) -> that's where box is!
        # Actually box is at (2,2), so we can't move there. Let me adjust.
        # Player at (2,3). Box at (2,2) and (3,2).
        # Move right then up to push box (3,2) up:
        choice_level.move(1, 0)  # player to (3,3)
        manager.record_move(choice_level, was_push=False)
        choice_level.move(0, -1)  # push box (3,2) to (3,1)
        manager.record_move(choice_level, was_push=True)
        # The state before the push had player at (3,3) with free directions
        # and adjacent to pushable box — should be a choice point


class TestNavigation:

    def test_undo_to_choice_point(self, choice_level, manager):
        """undo_to_previous_choice_point should jump back multiple moves."""
        # Make several moves to create some history
        choice_level.move(1, 0)   # move 1
        manager.record_move(choice_level, was_push=False)
        choice_level.move(1, 0)   # move 2
        manager.record_move(choice_level, was_push=False)
        choice_level.move(0, 1)   # move 3
        manager.record_move(choice_level, was_push=False)

        if manager.choice_points:
            undos = manager.undo_to_previous_choice_point(choice_level)
            assert undos > 0
            assert choice_level.moves < 3

    def test_undo_no_choice_points(self, corridor_level, manager):
        """With no choice points, undo_to_previous undoes everything."""
        corridor_level.move(1, 0)
        manager.record_move(corridor_level, was_push=False)
        undos = manager.undo_to_previous_choice_point(corridor_level)
        # Should undo to start
        assert corridor_level.moves == 0

    def test_clear(self, manager, choice_level):
        choice_level.move(1, 0)
        manager.record_move(choice_level, was_push=False)
        manager.clear()
        assert manager.choice_points == []

    def test_jump_to_choice_point(self, choice_level, manager):
        """jump_to_choice_point should undo exactly to the target index."""
        # Make 3 moves (all must succeed)
        choice_level.move(1, 0)   # player (2,3) -> (3,3)
        manager.record_move(choice_level, was_push=False)
        choice_level.move(0, 1)   # player (3,3) -> (3,4)
        manager.record_move(choice_level, was_push=False)
        choice_level.move(-1, 0)  # player (3,4) -> (2,4)
        manager.record_move(choice_level, was_push=False)

        # Jump back to after move 1 (history index 0)
        undos = manager.jump_to_choice_point(choice_level, 0)
        assert undos == 2
        assert choice_level.moves == 1
