"""Tests for core Level class: movement, undo, redo, reverse mode, reset, completion."""

import pytest
from src.core.level import Level


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_LEVEL = (
    "#####\n"
    "#@ .#\n"
    "#$  #\n"
    "#   #\n"
    "#####"
)

PUSH_LEVEL = (
    "#####\n"
    "#@$.#\n"
    "#####"
)

TWO_BOX_LEVEL = (
    "######\n"
    "#@ $.#\n"
    "#  $.#\n"
    "######"
)

COMPLETED_LEVEL = (
    "####\n"
    "#*@#\n"
    "####"
)


@pytest.fixture
def level():
    return Level(level_data=SIMPLE_LEVEL)


@pytest.fixture
def push_level():
    return Level(level_data=PUSH_LEVEL)


@pytest.fixture
def two_box():
    return Level(level_data=TWO_BOX_LEVEL)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

class TestLevelParsing:

    def test_dimensions(self, level):
        assert level.width == 5
        assert level.height == 5

    def test_player_pos(self, level):
        assert level.player_pos == (1, 1)

    def test_boxes_detected(self, level):
        assert (1, 2) in level.boxes

    def test_targets_detected(self, level):
        assert (3, 1) in level.targets

    def test_initial_counters_zero(self, level):
        assert level.moves == 0
        assert level.pushes == 0
        assert level.history == []
        assert level.redo_stack == []

    def test_walls(self, level):
        assert level.is_wall(0, 0)
        assert not level.is_wall(1, 1)

    def test_load_from_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Level(level_file="/nonexistent/file.txt")

    def test_must_provide_data_or_file(self):
        with pytest.raises(ValueError):
            Level()


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------

class TestMovement:

    def test_move_to_empty(self, level):
        assert level.move(1, 0)
        assert level.player_pos == (2, 1)
        assert level.moves == 1
        assert level.pushes == 0

    def test_move_blocked_by_wall(self, level):
        assert not level.move(0, -1)
        assert level.player_pos == (1, 1)
        assert level.moves == 0

    def test_push_box(self, push_level):
        # Player (1,1), box (2,1) -> push right
        assert push_level.move(1, 0)
        assert push_level.player_pos == (2, 1)
        assert (3, 1) in push_level.boxes
        assert push_level.pushes == 1

    def test_push_box_blocked_by_wall(self, push_level):
        # Push box right -> box at (3,1) hits target, push again -> wall at (4,1)
        push_level.move(1, 0)  # box to (3,1)
        assert not push_level.move(1, 0)  # box can't go to (4,1)=wall? Actually (4,1) is wall
        # Wait, let me check: PUSH_LEVEL = "#@$.#" so positions: #=wall(0), @=player(1), $=box(2), .=target(3), #=wall(4)
        # After push: player at (2,1), box at (3,1). Next push: box would go to (4,1)=wall -> blocked
        assert push_level.player_pos == (2, 1)

    def test_push_box_blocked_by_box(self, two_box):
        # Two boxes: (2,1) and (3,2). Push (2,1) right -> box at (3,1), then
        # can still move since (3,1) is empty before push
        assert two_box.move(1, 0)  # push box (2,1) to (3,1)

    def test_can_move_returns_false_for_wall(self, level):
        assert not level.can_move(0, -1)

    def test_can_move_returns_true_for_empty(self, level):
        assert level.can_move(1, 0)

    def test_multiple_moves(self, level):
        level.move(0, 1)  # down
        level.move(1, 0)  # right
        level.move(1, 0)  # right
        assert level.moves == 3
        assert level.player_pos == (3, 2)


# ---------------------------------------------------------------------------
# Undo / Redo
# ---------------------------------------------------------------------------

class TestUndoRedo:

    def test_undo_restores_state(self, level):
        original_pos = level.player_pos
        level.move(1, 0)
        assert level.undo()
        assert level.player_pos == original_pos
        assert level.moves == 0

    def test_undo_empty_history(self, level):
        assert not level.undo()

    def test_redo_after_undo(self, level):
        level.move(1, 0)
        pos_after_move = level.player_pos
        level.undo()
        assert level.redo()
        assert level.player_pos == pos_after_move
        assert level.moves == 1

    def test_redo_empty_stack(self, level):
        assert not level.redo()

    def test_new_move_clears_redo(self, level):
        level.move(1, 0)
        level.undo()
        assert len(level.redo_stack) == 1
        level.move(0, 1)  # different move
        assert len(level.redo_stack) == 0

    def test_undo_push_restores_box(self, push_level):
        original_boxes = list(push_level.boxes)
        push_level.move(1, 0)
        assert push_level.pushes == 1
        push_level.undo()
        assert push_level.boxes == original_boxes
        assert push_level.pushes == 0

    def test_redo_push_restores_box(self, push_level):
        push_level.move(1, 0)
        boxes_after = list(push_level.boxes)
        push_level.undo()
        push_level.redo()
        assert push_level.boxes == boxes_after
        assert push_level.pushes == 1

    def test_multiple_undo_redo(self, level):
        level.move(1, 0)
        level.move(0, 1)
        level.move(1, 0)
        assert level.moves == 3

        level.undo()
        level.undo()
        assert level.moves == 1
        assert len(level.redo_stack) == 2

        level.redo()
        assert level.moves == 2
        assert len(level.redo_stack) == 1


# ---------------------------------------------------------------------------
# Reverse Mode (Pull)
# ---------------------------------------------------------------------------

class TestReverseMode:

    def test_toggle(self, level):
        assert not level.reverse_mode
        assert level.toggle_reverse_mode() is True
        assert level.reverse_mode
        assert level.toggle_reverse_mode() is False

    def test_pull_moves_player(self):
        # #####
        # # $@#   player(3,1), box(2,1)
        # #####
        lvl = Level(level_data="#####\n# $@#\n#####")
        lvl.reverse_mode = True
        # Move left: player goes from (3,1) to (2,1)? No, (2,1) has a box.
        # In pull mode, player moves to (nx,ny)=(2,1) but that's where box is.
        # Player can't move onto a box even in pull mode.
        assert not lvl.move(-1, 0)

    def test_pull_drags_box_behind(self):
        # #####
        # #$@ #   player(2,1), box(1,1)
        # #####
        lvl = Level(level_data="#####\n#$@ #\n#####")
        lvl.reverse_mode = True
        # Move right: player (2,1)->(3,1), box behind at (1,1) follows to (2,1)
        assert lvl.move(1, 0)
        assert lvl.player_pos == (3, 1)
        assert (2, 1) in lvl.boxes
        assert lvl.pushes == 1

    def test_pull_no_box_behind(self):
        # ######
        # # @ $#   player(2,1), box(4,1)
        # ######
        lvl = Level(level_data="######\n# @ $#\n######")
        lvl.reverse_mode = True
        # Move left: player (2,1)->(1,1), behind=(3,1) which is empty
        assert lvl.move(-1, 0)
        assert lvl.player_pos == (1, 1)
        assert lvl.pushes == 0  # no pull happened

    def test_pull_undo(self):
        lvl = Level(level_data="#####\n#$@ #\n#####")
        lvl.reverse_mode = True
        original_boxes = list(lvl.boxes)
        lvl.move(1, 0)
        lvl.undo()
        assert lvl.boxes == original_boxes
        assert lvl.player_pos == (2, 1)

    def test_move_delegates_to_pull_in_reverse(self):
        lvl = Level(level_data="#####\n#$@ #\n#####")
        lvl.reverse_mode = True
        assert lvl.move(1, 0)
        assert lvl.player_pos == (3, 1)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

class TestReset:

    def test_reset_restores_initial(self, level):
        level.move(1, 0)
        level.move(0, 1)
        level.reset()
        assert level.player_pos == (1, 1)
        assert level.moves == 0
        assert level.pushes == 0
        assert level.history == []
        assert level.redo_stack == []

    def test_reset_no_history(self, level):
        level.reset()  # no-op
        assert level.player_pos == (1, 1)


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------

class TestCompletion:

    def test_not_completed_initially(self, push_level):
        assert not push_level.is_completed()

    def test_completed_when_box_on_target(self, push_level):
        push_level.move(1, 0)  # push box onto target
        assert push_level.is_completed()

    def test_already_completed(self):
        lvl = Level(level_data=COMPLETED_LEVEL)
        assert lvl.is_completed()


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

class TestDisplay:

    def test_get_display_char_player(self, level):
        assert level.get_display_char(1, 1) == '@'

    def test_get_display_char_box(self, level):
        assert level.get_display_char(1, 2) == '$'

    def test_get_display_char_target(self, level):
        assert level.get_display_char(3, 1) == '.'

    def test_get_display_char_wall(self, level):
        assert level.get_display_char(0, 0) == '#'

    def test_get_state_string(self, level):
        state = level.get_state_string(show_fess_coordinates=False)
        assert '@' in state
        assert '$' in state
